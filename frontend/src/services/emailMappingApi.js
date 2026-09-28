import { request } from './api';
import { workspacePath } from './admissionMappingApi';

export const runEmailMapping = (body, revision) =>
  request(`${workspacePath}/email-mapping/run`, { method: 'POST', body, revision });

export const runFullNameClassMapping = (body, revision) =>
  request(`${workspacePath}/full-name-class-mapping/run`, { method: 'POST', body, revision });

/*
 * Purpose: Exposes the two specialized mapping commands that follow admission mapping.
 * runEmailMapping sends selected email and name columns to the email-mapping endpoint.
 * runFullNameClassMapping sends full-name and class selections to its mapping endpoint.
 * Both operations use the shared mapping workspace and return its updated state.
 * Both include the current revision so stale browser tabs receive a conflict response.
 * Used by: EmailForm when the user starts the email-mapping operation.
 * FullNameClassMappingPage calls the full-name and class mapping operation.
 * Both calls run through WorkspaceContext's mutation wrapper for UI state and recovery.
 */
