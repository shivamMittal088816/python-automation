"""Names of workflow input files, export stages and handoff sources."""

FILES = {'school':'saved_admission_school', 'dump':'saved_admission_dump', 'email_dump':'saved_email_dump'}


STAGES = {'admission':'admission_exports', 'email':'email_exports', 'full_name_class':'full_name_class_exports'}


SOURCES = {'Admission mapping — Not matched':('admission_exports','not_matched.xlsx'),
           'Email mapping — Not matched':('email_exports','email_not_matched.xlsx')}
