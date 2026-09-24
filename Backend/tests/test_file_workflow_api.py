"""Exercise HTTP file workflows against the existing Python operations, without SQL writes."""
import asyncio
from io import BytesIO
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

import pandas as pd
from openpyxl import load_workbook

from Backend.main import create_app
from Backend.api import file_workflow_state as state_store
from Backend.routes.file_workflow_routes import email_mapping, file_inputs


async def asgi_request(app, method, path, body=b'', headers=None):
    headers = list(headers or [])
    if getattr(app.state, 'test_cookie', None) and not any(key == b'cookie' for key, _ in headers):
        headers.append((b'cookie', app.state.test_cookie))
    route, _, query = path.partition('?')
    messages = []
    scope = {'type':'http','asgi':{'version':'3.0'},'http_version':'1.1','method':method,
        'scheme':'http','path':route,'raw_path':route.encode(),'query_string':query.encode(),
        'root_path':'','headers':headers or [],'server':('localhost',80),'client':('localhost',1234)}
    async def receive():
        return {'type':'http.request','body':body,'more_body':False}
    async def send(message):
        messages.append(message)
    await app(scope, receive, send)
    status = next(message['status'] for message in messages if message['type']=='http.response.start')
    response_headers = dict(next(message['headers'] for message in messages if message['type']=='http.response.start'))
    if b'set-cookie' in response_headers:
        app.state.test_cookie = response_headers[b'set-cookie'].split(b';', 1)[0]
    data = b''.join(message.get('body',b'') for message in messages if message['type']=='http.response.body')
    return status, response_headers, data


class FileWorkflowAPITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)
        for module, folder in ((state_store,root/'sessions'),):
            replacement = patch.object(module,'ROOT',folder)
            replacement.start()
            self.addCleanup(replacement.stop)
        self.app = create_app()
        self.school = pd.DataFrame({'admission_number':['001','002','003'],
            'first_name':['Alice','Bob','Carol'],'full_name':['Alice Smith','Bob Jones','Carol Lee'],
            'email':['alice@example.test','bob@example.test','carol@example.test'],
            'classNumber':['3','4','5'],'class':['Class III','Class IV','Class V'],
            'section':['A','B','C'],'package':['Foundation','Advanced','Foundation']})
        self.dump = pd.DataFrame({'admission_number':['001','999','888'],
            'user_firstname':['Alice','Bob','Carol'],'user_lastname':['Smith','Jones','Lee'],
            'fullname':['Alice Smith','Bob Jones','Carol Lee'],'user_name':['alice','bob','carol'],
            'user_id':['0001','0002','0003'],'user_email':self.school.email,
            'generated_col':['alicesmith3','bobjones4','carollee5'],
            'user_edu_class':['2','3','4'],'user_edu_major':['A','B','C']})
        self.json('POST','/mapping/session',{})
        self.id = self.app.state.test_cookie.decode().split('=', 1)[1]

    def json(self,method,path,payload=None,expected=200,headers=None):
        body=json.dumps(payload).encode() if payload is not None else b''
        status,_,data=asyncio.run(asgi_request(self.app,method,'/api/v1'+path,body,
            [(b'content-type',b'application/json')]+(headers or [])))
        self.assertEqual(status,expected,data.decode(errors='replace'))
        return json.loads(data)

    def endpoint(self,suffix=''):
        return '/mapping'+(suffix or '/session')

    def upload(self,kind,filename,data,save_index=True):
        boundary='mapping-test-boundary'
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="{filename}"\r\n'
              'Content-Type: application/octet-stream\r\n\r\n').encode()+data+f'\r\n--{boundary}--\r\n'.encode()
        status,_,response=asyncio.run(asgi_request(self.app,'POST','/api/v1'+self.endpoint('/files/'+kind),body,
            [(b'content-type',f'multipart/form-data; boundary={boundary}'.encode())]))
        self.assertEqual(status,200,response.decode(errors='replace'))
        if kind == "dump" and save_index:
            return self.json("PATCH",self.endpoint("/school"),{"school_index":"914"})
        return json.loads(response)

    def inputs(self):
        self.upload('school','school.csv',self.school.to_csv(index=False).encode())
        return self.upload('dump','dump.csv',self.dump.to_csv(index=False).encode())

    def mapped(self):
        self.inputs()
        return self.json('POST',self.endpoint('/admission-mapping/run'))

    def test_run_submits_columns_and_preview_does_not_save_them(self):
        before = self.mapped()
        choices = {'school_admission_col': 'email', 'school_name_col': 'full_name'}
        preview = self.json('POST', self.endpoint('/configuration-preview'), choices)
        self.assertEqual(preview['settings']['school_name_col'], 'full_name')
        saved = self.json('GET', self.endpoint())
        self.assertEqual(saved['settings'], before['settings'])
        self.assertEqual(saved['run_columns'], before['run_columns'])
        from Backend.routes.file_workflow_routes import admission_mapping
        with patch.object(admission_mapping, 'map_students', side_effect=ValueError('failed')):
            self.json('POST', self.endpoint('/admission-mapping/run'), choices, expected=422)
        saved = self.json('GET', self.endpoint())
        self.assertEqual(saved['settings'], before['settings'])
        self.assertEqual(saved['export_versions'], before['export_versions'])
        result = self.json('POST', self.endpoint('/admission-mapping/run'), choices)
        self.assertEqual(result['run_columns']['admission']['1'], ['email', 'full_name'])
        self.assertEqual(result['settings']['school_admission_col'], 'email')

    def test_uploaded_dump_requires_saved_school_index_before_mapping(self):
        self.upload('school','school.csv',self.school.to_csv(index=False).encode())
        data=self.dump.to_csv(index=False).encode()
        self.upload('dump','dump.csv',data,save_index=False)
        for endpoint, payload in (('/admission-mapping/run', None),
                                  ('/email-mapping/run', {'email_column':'email','name_column':'first_name'}),
                                  ('/full-name-class-mapping/run', {'source':'Admission mapping \u2014 Not matched','name_column':'full_name','class_column':'classNumber'})):
            result=self.json('POST',self.endpoint(endpoint),payload,expected=422)
            self.assertIn('school index', result['detail'])
        for index in ('', ' ', 'abc', '-1'):
            self.json('PATCH',self.endpoint('/school'),{'school_index':index},expected=422)
        saved=self.json('PATCH',self.endpoint('/school'),{'school_index':'914'})
        self.assertEqual(saved['files']['dump']['school_index'],'914')
        self.assertEqual(self.json('GET',self.endpoint())['files']['dump']['school_index'],'914')
        self.assertEqual(self.json('POST',self.endpoint('/admission-mapping/run'))['exports']['admission']['matched.xlsx'],1)
        self.upload('dump','replacement.csv',data,save_index=False)
        self.json('POST',self.endpoint('/admission-mapping/run'),expected=422)

    def test_removed_jobs_and_review_endpoints_are_unavailable(self):
        routes = [('GET','/mapping/jobs'),('GET','/mapping/jobs/1'),
                  ('GET','/mapping/results'),('GET','/mapping/results/1'),
                  ('POST','/mapping/results/1/approve'),('POST','/mapping/results/1/reject'),
                  ('PATCH','/mapping/results/1'),('PATCH','/mapping/results/bulk')]
        paths = self.app.openapi()['paths']
        self.assertFalse(any('/mapping/jobs' in path or '/mapping/results' in path for path in paths))
        for method,path in routes:
            with self.subTest(method=method,path=path):
                self.json(method,path,{} if method != 'GET' else None,expected=404)

    def test_health_and_student_listing_remain_available(self):
        self.assertTrue(self.json('GET','/mapping/health')['success'])
        from Backend.routes import student_mapping
        class Students:
            def get_students(self, cursor=None, limit=25):
                self.arguments=(cursor,limit)
                return {'data':[{'user_id':'001','user_firstname':'Alice'}],
                        'pagination':{'limit':limit,'next_cursor':'001'}}
        repository=Students()
        self.app.dependency_overrides[student_mapping.get_db]=lambda: None
        with patch.object(student_mapping,'UserStudentRepository',return_value=repository):
            result=self.json('GET','/mapping/students?cursor=9&limit=2')
        self.assertEqual(repository.arguments,(9,2))
        self.assertEqual(result['data'][0]['first_name'],'Alice')
        self.assertEqual(result['data'][0]['user_id'],'001')
        self.assertEqual(result['pagination'],{'limit':2,'next_cursor':'001'})
        self.json('GET','/mapping/students?limit=0',expected=422)
        self.json('GET','/mapping/students?limit=101',expected=422)

    def test_empty_upload_is_rejected_without_replacing_state(self):
        boundary='mapping-test-boundary'
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="school.csv"\r\n'
              'Content-Type: text/csv\r\n\r\n\r\n'
              f'--{boundary}--\r\n').encode()
        status,_,response=asyncio.run(asgi_request(
            self.app,'POST','/api/v1'+self.endpoint('/files/school'),body,
            [(b'content-type',f'multipart/form-data; boundary={boundary}'.encode())]))
        self.assertEqual(status,422,response.decode(errors='replace'))
        self.assertIn('empty',json.loads(response)['detail'].lower())
        self.assertNotIn('school',self.json('GET',self.endpoint())['files'])

    def test_admission_workflow_preserves_identifiers_and_download_bytes(self):
        result=self.mapped()
        self.assertEqual(result['exports']['admission'],{'matched.xlsx':1,'review.xlsx':0,'not_matched.xlsx':2})
        preview=self.json('GET',self.endpoint('/result-previews/admission/matched.xlsx'))
        self.assertEqual(preview['rows'][0]['mapping_admission_number'],'001')
        self.assertEqual(preview['rows'][0]['mapping_user_id'],'0001')
        self.assertEqual(preview['columns'][:2], ['admission_number', 'first_name'])
        self.assertEqual(preview['column_labels']['mapping_dump_first_name'], 'dump_user_firstname')
        self.assertEqual(preview['column_labels']['mapping_username'], 'dump_user_name')
        self.assertEqual(preview['column_labels']['mapping_user_id'], 'dump_user_id')
        for column in self.school.columns:
            self.assertEqual(preview['column_labels'].get(column, column), column)
        status,headers,body=asyncio.run(asgi_request(self.app,'GET','/api/v1'+self.endpoint('/downloads/admission?filename=matched.xlsx&format=xlsx')))
        self.assertEqual(status,200)
        with state_store.workspace(self.id,persist=False) as state:
            self.assertEqual(body,state['admission_exports']['matched.xlsx']['data'])
        self.assertIn(b'matched.xlsx',headers[b'content-disposition'])
        status,_,body=asyncio.run(asgi_request(self.app,'GET','/api/v1'+self.endpoint('/downloads/admission?filename=matched.xlsx&format=csv')))
        self.assertEqual(status,200)
        self.assertTrue(body.startswith(b'\xef\xbb\xbf'))
        self.assertIn('0001',body.decode('utf-8-sig'))

    def test_admission_preview_uses_actual_dump_headers(self):
        self.school = self.school.rename(columns={'first_name': 'FIRST NAME'})
        self.dump = self.dump.rename(columns={'user_firstname': 'First Name', 'user_name': 'Username'})
        self.mapped()
        for filename in ('matched.xlsx', 'review.xlsx', 'not_matched.xlsx'):
            preview = self.json('GET', self.endpoint('/result-previews/admission/' + filename))
            self.assertIn('FIRST NAME', preview['columns'])
            self.assertNotIn('FIRST NAME', preview['column_labels'])
            self.assertEqual(preview['column_labels']['mapping_dump_first_name'], 'dump_First Name')
            self.assertEqual(preview['column_labels']['mapping_username'], 'dump_Username')

    def test_admission_preview_includes_dump_fullname_for_saved_results(self):
        self.mapped()
        preview = self.json('GET', self.endpoint('/result-previews/admission/matched.xlsx'))
        self.assertIn('mapping_dump_full_name', preview['columns'])
        self.assertEqual(preview['column_labels']['mapping_dump_full_name'], 'dump_fullname')
        self.assertEqual(preview['rows'][0]['mapping_dump_full_name'], 'Alice Smith')
        self.assertEqual(preview['rows'][0]['full_name'], 'Alice Smith')
        unmatched = self.json('GET', self.endpoint('/result-previews/admission/not_matched.xlsx'))
        self.assertTrue(all(row['mapping_dump_full_name'] == '' for row in unmatched['rows']))

    def test_admission_preview_fullname_shows_duplicate_candidates(self):
        self.dump.loc[1, 'admission_number'] = '001'
        self.mapped()
        preview = self.json('GET', self.endpoint('/result-previews/admission/review.xlsx'))
        self.assertEqual(preview['rows'][0]['mapping_dump_full_name'], 'Alice Smith\nBob Jones')

    def test_preview_transfers_are_locked_and_preserve_all_results(self):
        before=self.mapped()
        for source in ('matched.xlsx','review.xlsx','not_matched.xlsx'):
            preview=self.json('GET',self.endpoint('/result-previews/admission/'+source))
            for destination in ('matched.xlsx','review.xlsx','not_matched.xlsx'):
                if source == destination:
                    continue
                with self.subTest(source=source,destination=destination):
                    response=self.json('POST',self.endpoint('/admission-mapping/move'),{
                        'filename':source,'selected_rows':[0],'destination':destination,
                        'version':preview['version']},expected=403)
                    self.assertIn('locked',response['detail'])
        after=self.json('GET',self.endpoint(''))
        self.assertEqual(after['exports'],before['exports'])
        self.assertEqual(after['export_versions'],before['export_versions'])

    def test_admission_second_pass_requires_first_pass_and_preserves_results(self):
        self.school.loc[0, 'first_name'] = 'Wrong'
        self.school.loc[0, 'full_name'] = 'SMITHALICE'
        self.inputs()
        payload = {'name_column': 'full_name'}
        blocked = self.json('POST', self.endpoint('/admission-mapping/second-pass'), payload, expected=422)
        self.assertIn('pass 1', blocked['detail'])
        self.json('POST', self.endpoint('/admission-mapping/run'))
        self.json('POST', self.endpoint('/admission-mapping/second-pass'), {'name_column': 'invalid'}, expected=422)
        before = self.json('GET', self.endpoint())
        self.assertEqual(before['admission_result_pass'], 1)
        result = self.json('POST', self.endpoint('/admission-mapping/second-pass'), payload)
        self.assertEqual(result['admission_result_pass'], 2)
        self.assertEqual(result['run_columns']['admission']['2'], ['admission_number', payload['name_column']])
        self.assertEqual(result['exports']['admission'], {'matched.xlsx': 1, 'review.xlsx': 0, 'not_matched.xlsx': 2})
        self.assertEqual(result['export_versions']['admission']['not_matched.xlsx'], before['export_versions']['admission']['not_matched.xlsx'])
        preview = self.json('GET', self.endpoint('/result-previews/admission/matched.xlsx'))
        self.assertEqual(preview['rows'][0]['mapping_user_id'], '0001')
        self.assertIn('Pass 2', preview['rows'][0]['mapping_status'])
        saved = self.json('GET', self.endpoint())
        self.assertEqual(saved['exports']['admission'], result['exports']['admission'])
        self.assertEqual(saved['admission_result_pass'], 2)
        again = self.json('POST', self.endpoint('/admission-mapping/second-pass'), payload)
        self.assertEqual(again['exports']['admission'], result['exports']['admission'])
        rerun = self.json('POST', self.endpoint('/admission-mapping/run'))
        self.assertEqual(rerun['admission_result_pass'], 1)
        self.json('PUT', self.endpoint('/settings'), {'settings': {'school_name_col': 'full_name'}}, expected=404)

    def test_admission_second_pass_checks_duplicate_accounts(self):
        self.school.loc[0, 'first_name'] = 'Wrong'
        self.dump.loc[1, 'admission_number'] = '002'
        self.dump.loc[1, 'user_id'] = '0001'
        self.mapped()
        result = self.json('POST', self.endpoint('/admission-mapping/second-pass'), {'name_column': 'full_name'})
        self.assertEqual(result['exports']['admission']['matched.xlsx'], 0)
        self.assertEqual(result['exports']['admission']['review.xlsx'], 2)
        preview = self.json('GET', self.endpoint('/result-previews/admission/review.xlsx'))
        self.assertTrue(all('Duplicate username or user ID' in row['mapping_status'] for row in preview['rows']))

    def test_email_and_full_name_stages_use_existing_services(self):
        self.mapped()
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        self.dump['user_edu_school']='914'
        source=self.json('GET',self.endpoint('/table-previews/admission_source'))
        self.assertEqual(source['suggestions']['full_name_column'],'full_name')
        with patch.object(email_mapping,'fetch_email_dump',return_value=self.dump.iloc[1:2]) as fetch:
            result=self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'})
        self.assertEqual(fetch.call_count,1)
        self.assertEqual(result['exports']['email']['email_matched.xlsx'],1)
        self.assertEqual(result['exports']['email']['email_not_matched.xlsx'],1)
        result=self.json('POST',self.endpoint('/full-name-class-mapping/run'),{'source':'Email mapping — Not matched','name_column':'full_name','class_column':'classNumber'})
        self.assertEqual(result['exports']['full_name_class']['full_name_class_matched.xlsx'],1)
        self.assertIn('email_dump',result['files'])

    def test_email_second_pass_uses_saved_dump_and_persists(self):
        self.mapped()
        self.json('POST', self.endpoint('/email-mapping/second-pass'), expected=422)
        dump = self.dump.iloc[1:2].copy()
        dump['user_firstname'] = 'Robert'
        dump['fullname'] = 'BobJones'
        dump['user_edu_school'] = '914'
        with patch.object(email_mapping, 'fetch_email_dump', return_value=dump) as fetch:
            first = self.json('POST', self.endpoint('/email-mapping/run'), {'email_column': 'email', 'name_column': 'first_name'})
            self.assertEqual(first['exports']['email']['email_review.xlsx'], 1)
            self.assertEqual(first['email_result_pass'], 1)
            second = self.json('POST', self.endpoint('/email-mapping/second-pass'), {'name_column': 'full_name'})
            self.assertEqual(fetch.call_count, 1)
        self.assertEqual(second['exports']['email']['email_matched.xlsx'], 1)
        self.assertEqual(second['exports']['email']['email_review.xlsx'], 0)
        saved = self.json('GET', self.endpoint())
        self.assertEqual(saved['exports']['email'], second['exports']['email'])
        self.assertTrue(saved['email_pass_one_complete'])
        self.assertEqual(saved['email_result_pass'], 2)
        self.assertEqual(saved['run_columns']['email'], {'1':['email','first_name'], '2':['full_name']})
        with patch.object(email_mapping, 'fetch_email_dump', return_value=dump):
            rerun = self.json('POST', self.endpoint('/email-mapping/run'), {'email_column': 'email', 'name_column': 'first_name'})
        self.assertEqual(rerun['email_result_pass'], 1)

    def test_email_match_from_another_school_goes_to_review(self):
        self.mapped()
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        dump=self.dump.iloc[1:2].copy()
        dump['user_edu_school']='915'
        with patch.object(email_mapping,'fetch_email_dump',return_value=dump):
            result=self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'})
        self.assertEqual(result['exports']['email']['email_matched.xlsx'],0)
        self.assertEqual(result['exports']['email']['email_review.xlsx'],1)
        rows=self.json('GET',self.endpoint('/result-previews/email/email_review.xlsx'))['rows']
        self.assertIn('user_edu_school differs',rows[0]['email_mapping_status'])

    def test_account_conflicts_reconcile_all_stages(self):
        self.mapped()
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        self.dump['user_edu_school']='914'
        conflicting=self.dump.iloc[1:2].copy()
        conflicting['user_id']='0001'
        with patch.object(email_mapping,'fetch_email_dump',return_value=conflicting):
            result=self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'})
        self.assertEqual(result['exports']['admission']['matched.xlsx'],0)
        self.assertEqual(result['exports']['admission']['review.xlsx'],1)
        self.assertEqual(result['exports']['email']['email_review.xlsx'],1)

    def test_email_handoff_and_missing_column_validation(self):
        self.mapped()
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        self.dump['user_edu_school']='914'
        with patch.object(email_mapping,'fetch_email_dump',return_value=self.dump.iloc[1:2]):
            mapped=self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'})
        self.assertEqual(mapped['exports']['email']['email_matched.xlsx'],1)
        self.upload('school','school.csv',self.school.iloc[:2].to_csv(index=False).encode())
        changed=self.json('POST',self.endpoint('/admission-mapping/run'))
        self.assertEqual(changed['exports']['email'],{})
        self.assertNotIn('email_dump',changed['files'])
        self.upload('school','school.csv',self.school.drop(columns='email').to_csv(index=False).encode())
        self.json('POST',self.endpoint('/admission-mapping/run'))
        source=self.json('GET',self.endpoint('/table-previews/admission_source'))
        self.assertIsNone(source['suggestions']['email_column'])
        with patch.object(email_mapping,'fetch_email_dump') as fetch:
            self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'},expected=422)
        fetch.assert_not_called()

    def test_conflicting_review_cannot_be_manually_promoted(self):
        self.mapped()
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        self.dump['user_edu_school']='914'
        conflicting=self.dump.iloc[1:2].copy()
        conflicting['user_id']='0001'
        with patch.object(email_mapping,'fetch_email_dump',return_value=conflicting):
            self.json('POST',self.endpoint('/email-mapping/run'),{'email_column':'email','name_column':'first_name'})
        preview=self.json('GET',self.endpoint('/result-previews/admission/review.xlsx'))
        self.json('POST',self.endpoint('/admission-mapping/move'),{'filename':'review.xlsx','selected_rows':[0],'destination':'matched.xlsx','version':preview['version']},expected=403)
        # Locked previews preserve the account conflict classifications.
        result=self.json('POST',self.endpoint('/duplicate-accounts/reconcile'))
        self.assertEqual(result['exports']['admission']['matched.xlsx'],0)

    def test_result_versions_change_when_counts_stay_the_same(self):
        before=self.mapped()
        changed=self.dump.copy()
        changed.loc[0,'user_id']='different-id'
        self.upload('dump','dump.csv',changed.to_csv(index=False).encode())
        after=self.json('POST',self.endpoint('/admission-mapping/run'))
        self.assertEqual(before['exports'],after['exports'])
        self.assertNotEqual(before['export_versions']['admission']['matched.xlsx'],after['export_versions']['admission']['matched.xlsx'])
        self.assertNotEqual(before['files']['dump']['version'],after['files']['dump']['version'])

    def test_full_name_second_round_retries_misses_and_survives_reload(self):
        self.school.loc[1,'full_name']='Jones Bob'
        self.dump['user_edu_class']=['3','4','5']
        self.mapped()
        payload={'source':'Admission mapping — Not matched','name_column':'full_name','class_column':'classNumber'}
        second={**payload,'round':2}
        rejected=self.json('POST',self.endpoint('/full-name-class-mapping/run'),second,expected=422)
        self.assertIn('1st round',rejected['detail'])
        first=self.json('POST',self.endpoint('/full-name-class-mapping/run'),payload)
        self.assertEqual(first['exports']['full_name_class']['full_name_class_matched.xlsx'],1)
        self.assertEqual(first['full_name_class_round_one_not_matched'],1)
        self.assertEqual(first['full_name_class_round'],1)
        self.json('POST',self.endpoint('/full-name-class-mapping/run'),{**second,'class_column':'missing'},expected=422)
        after_error=self.json('GET',self.endpoint())
        self.assertEqual(after_error['export_versions'],first['export_versions'])
        result=self.json('POST',self.endpoint('/full-name-class-mapping/run'),second)
        self.assertEqual(result['full_name_class_round'],2)
        self.assertEqual(result['exports']['full_name_class']['full_name_class_matched.xlsx'],2)
        self.assertEqual(result['exports']['full_name_class']['full_name_class_not_matched.xlsx'],0)
        matched=self.json('GET',self.endpoint('/result-previews/full_name_class/full_name_class_matched.xlsx'))
        self.assertEqual([row['full_name'] for row in matched['rows']],['Carol Lee','Jones Bob'])
        self.assertEqual([row['full_name_class_user_id'] for row in matched['rows']],['0003','0002'])
        self.assertNotIn('Round 2',matched['rows'][0]['full_name_class_status'])
        self.assertIn('Round 2',matched['rows'][1]['full_name_class_status'])
        self.assertEqual(self.json('POST',self.endpoint('/full-name-class-mapping/run'),second)['exports'],result['exports'])
        status,_,body=asyncio.run(asgi_request(self.app,'GET','/api/v1'+self.endpoint('/downloads/full_name_class?filename=full_name_class_matched.xlsx&format=csv')))
        self.assertEqual(status,200)
        self.assertIn('Jones Bob',body.decode('utf-8-sig'))
        self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Round Test'})
        restored=self.json('GET',self.endpoint())
        self.id=self.app.state.test_cookie.decode().split('=', 1)[1]
        self.assertEqual(restored['exports'],result['exports'])
        self.assertEqual(restored['full_name_class_round'],2)
        self.assertEqual(restored['full_name_class_round_one_not_matched'],1)
        self.assertEqual(self.json('POST',self.endpoint('/full-name-class-mapping/run'),second)['exports'],result['exports'])
        # A different school name column replaces round 2, retaining round 1.
        changed=self.json('POST',self.endpoint('/full-name-class-mapping/run'),{**second,'name_column':'first_name'})
        self.assertEqual(changed['exports']['full_name_class']['full_name_class_matched.xlsx'],1)
        self.assertEqual(changed['run_columns']['full_name_class'], {'1':['full_name','classNumber'], '2':['first_name','classNumber']})
        self.assertEqual(changed['exports']['full_name_class']['full_name_class_not_matched.xlsx'],1)
        rerun=self.json('POST',self.endpoint('/full-name-class-mapping/run'),payload)
        self.assertEqual(rerun['full_name_class_round'],1)
        self.assertEqual(rerun['exports']['full_name_class'],first['exports']['full_name_class'])

    def test_second_round_keeps_cross_round_duplicate_account_protection(self):
        self.school.loc[1,'full_name']='Jones Bob'
        self.dump['user_edu_class']=['3','4','5']
        self.dump.loc[1,'user_id']='0003'
        self.mapped()
        payload={'source':'Admission mapping — Not matched','name_column':'full_name','class_column':'classNumber'}
        self.json('POST',self.endpoint('/full-name-class-mapping/run'),payload)
        result=self.json('POST',self.endpoint('/full-name-class-mapping/run'),{
            **payload,'round':2})
        self.assertEqual(result['exports']['full_name_class']['full_name_class_matched.xlsx'],0)
        self.assertEqual(result['exports']['full_name_class']['full_name_class_review.xlsx'],2)

    def test_literal_scoped_search_and_overviews(self):
        self.inputs()
        path=self.endpoint('/table-previews/school?')+urlencode({'query':'Alice','columns':'first_name','class_column':'class','section_column':'section'})
        table=self.json('GET',path)
        self.assertEqual(table['found'],1)
        self.assertEqual(table['overview'][0],{'Class':'Class III','Students':1,'Sections':'A'})
        self.assertEqual(self.json('GET',self.endpoint('/table-previews/school?query=%5B'))['found'],0)
        dump=self.json('GET',self.endpoint('/table-previews/dump'))
        self.assertEqual(dump['overview'][0]['Class'],'Class 3')
        self.assertEqual(dump['student_count'],3)

    def test_named_sheets_and_setting_invalidation(self):
        buffer=BytesIO()
        with pd.ExcelWriter(buffer,engine='openpyxl') as writer:
            self.school.iloc[:0].to_excel(writer,sheet_name='Empty',index=False)
            self.school.to_excel(writer,sheet_name='Students',index=False)
        self.upload('school','school.xlsx',buffer.getvalue())
        self.upload('dump','dump.csv',self.dump.to_csv(index=False).encode())
        result=self.json('POST',self.endpoint('/admission-mapping/run'),{'admission_school_sheet':'Students'})
        self.assertEqual(result['exports']['admission']['matched.xlsx'],1)
        self.json('POST',self.endpoint('/configuration-preview'),{'admission_school_sheet':'Empty'})
        result=self.json('GET',self.endpoint())
        self.assertEqual(result['exports']['admission']['matched.xlsx'],1)
        result=self.json('POST',self.endpoint('/admission-mapping/run'),{'admission_school_sheet':'Empty'})
        self.assertEqual(result['exports']['admission']['matched.xlsx'],0)

    def test_draft_dropdowns_preserve_all_files_through_session_reload(self):
        self.mapped()
        self.json('PATCH', self.endpoint('/school'), {'school_index':'914','school_name':'Draft Test'})
        with patch.object(email_mapping, 'fetch_email_dump', return_value=self.dump.iloc[1:2]):
            self.json('POST', self.endpoint('/email-mapping/run'), {'email_column':'email','name_column':'first_name'})
        before = self.json('POST', self.endpoint('/full-name-class-mapping/run'), {
            'source':'Email mapping — Not matched','name_column':'full_name','class_column':'classNumber'})
        folder = state_store.ROOT / self.id
        original_files = {p.name:p.read_bytes() for p in folder.glob('*.bin')}
        session_path = state_store.ROOT / self.id / 'state.json'
        original_state = json.loads(session_path.read_text())
        changes = {'school_name_col':'full_name', 'school_admission_col':'email',
                   'email_full_name_column':'first_name', 'full_name_class_class_column':'section',
                   'admission_dump_source':'Fetch from SQL', 'admission_dump_school_index':'999'}
        self.json('POST', self.endpoint('/configuration-preview'), changes)
        changed = self.json('GET', self.endpoint())
        for response in (changed, self.json('GET', self.endpoint())):
            self.assertEqual(response['export_versions'], before['export_versions'])
            self.assertEqual(response['run_columns'], before['run_columns'])
            self.assertEqual(response['files'], before['files'])
        saved_state = json.loads(session_path.read_text())
        for key in state_store.FILE_KEYS + state_store.EXPORT_KEYS:
            self.assertEqual(saved_state.get(key), original_state.get(key))
        self.assertEqual({p.name:p.read_bytes() for p in folder.glob('*.bin')}, original_files)
        restored = self.json('GET', self.endpoint())
        self.assertEqual(restored['export_versions'], before['export_versions'])
        self.assertEqual(restored['settings']['school_name_col'], before['settings']['school_name_col'])
        self.assertEqual(restored['run_columns'], before['run_columns'])
        after = self.json('POST', self.endpoint('/admission-mapping/run'), changes)
        self.assertEqual(after['exports']['email'], {})
        self.assertEqual(after['exports']['full_name_class'], {})
        self.assertNotEqual(after['exports']['admission'], before['exports']['admission'])
        self.assertEqual(after['run_columns']['admission']['1'], ['email', 'full_name'])
        self.assertEqual(after['run_columns']['email'], {})
        self.assertEqual(after['run_columns']['full_name_class'], {})

    def test_dump_fetch_persists_latest_school_search_index(self):
        for index in ('914', '915'):
            dump = self.dump.copy()
            dump.attrs.update(school_index=index, school_name='Test School')
            with patch.object(file_inputs, 'fetch_school_dump', return_value=dump):
                self.json('POST', self.endpoint('/student-dump/fetch'), {'school_index': ' ' + index + ' '})
            restored = self.json('GET', self.endpoint())
            self.assertEqual(restored['files']['dump']['school_index'], index)
            self.assertEqual(restored['settings']['admission_dump_school_index'], index)
            self.assertEqual(restored['settings']['admission_dump_source'], 'Fetch from SQL')
            saved = json.loads((state_store.ROOT / self.id / 'state.json').read_text())
            self.assertEqual(saved['admission_settings']['admission_dump_school_index'], index)

    def test_workspace_survives_reload_but_new_session_starts_empty(self):
        self.mapped()
        result=self.json('PATCH',self.endpoint('/school'),{'school_index':'914','school_name':'Test School'})
        self.assertEqual(result['files']['dump']['school_index'],'914')
        cookie=self.app.state.test_cookie
        self.app=create_app()
        self.app.state.test_cookie=cookie
        result=self.json('GET',self.endpoint())
        self.assertEqual(result['exports']['admission']['matched.xlsx'],1)
        school_root = Path(self.temp.name) / 'schools'
        self.assertFalse(school_root.exists())
        # Even an existing school snapshot must not populate a new session.
        folder = school_root / '914-Test School'
        folder.mkdir(parents=True)
        (folder / 'dump.csv').write_bytes(b'admission_number\n001\n')
        school_files = {p.relative_to(school_root): p.read_bytes()
                        for p in school_root.rglob('*') if p.is_file()}
        restored=self.json('POST','/mapping/session',{'school_index':'914'})
        self.assertEqual(restored['exports']['admission'], {})
        self.assertFalse(restored['files'].get('dump'))
        self.assertEqual({p.relative_to(school_root): p.read_bytes()
                          for p in school_root.rglob('*') if p.is_file()}, school_files)

    def test_local_path_loading_and_disable_switch(self):
        path=Path(self.temp.name)/'school.csv'
        path.write_bytes(self.school.to_csv(index=False).encode())
        result=self.json('POST',self.endpoint('/files/school/path'),{'path':str(path)})
        self.assertEqual(result['files']['school']['name'],'school.csv')
        with patch.object(file_inputs.settings,'ALLOW_LOCAL_FILE_PATHS',False):
            self.json('POST',self.endpoint('/files/school/path'),{'path':str(path)},expected=403)

    def test_failed_sql_fetch_preserves_previous_dump_and_results(self):
        before=self.mapped()
        failures=((ConnectionError('internal connection details'),503),
                  (ValueError('No school found for index 999999.'),422))
        for failure,status in failures:
            with self.subTest(status=status), patch.object(file_inputs,'fetch_school_dump',side_effect=failure):
                response=self.json('POST',self.endpoint('/student-dump/fetch'),{'school_index':'999999'},expected=status)
                result=self.json('GET',self.endpoint())
                self.assertEqual(result['files']['dump'],before['files']['dump'])
                self.assertEqual(result['export_versions']['admission'],before['export_versions']['admission'])
                if status == 503:
                    self.assertNotIn('internal connection details',str(response))

    def test_invalid_input_and_missing_sessions(self):
        self.json('PUT',self.endpoint('/settings'),{'settings':{'unexpected':1}},expected=404)
        self.assertNotIn('/api/v1/mapping/settings', self.app.openapi()['paths'])
        self.json('GET','/mapping/sessions/not-a-uuid',expected=404)
        self.json('POST',self.endpoint('/admission-mapping/run'),expected=422)
        self.inputs()
        self.json('GET',self.endpoint('/table-previews/school?columns=missing'),expected=422)

    def test_download_conversion_escapes_formula_cells(self):
        self.upload('dump','dump.csv',b'value\n=1+1\n')
        status,_,body=asyncio.run(asgi_request(self.app,'GET','/api/v1'+self.endpoint('/downloads/dump?format=xlsx')))
        self.assertEqual(status,200)
        workbook=load_workbook(BytesIO(body))
        self.assertEqual(workbook.active['A2'].value,'=1+1')
        self.assertEqual(workbook.active['A2'].data_type,'s')
        workbook.close()

    def test_cors_is_limited_to_configured_origins(self):
        for origin,expected in ((b'http://localhost:5173',200),(b'https://untrusted.example',400)):
            status,headers,_=asyncio.run(asgi_request(self.app,'OPTIONS','/api/v1/mapping/sessions',headers=[
                (b'origin',origin),(b'access-control-request-method',b'POST')]))
            self.assertEqual(status,expected)
            if expected==200: self.assertEqual(headers[b'access-control-allow-origin'],origin)


if __name__=='__main__':
    unittest.main()
