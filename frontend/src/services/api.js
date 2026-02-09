const API_BASE = process.env.REACT_APP_API_URL || '/api';

class ApiService {
  constructor() {
    this.token = localStorage.getItem('ns_token');
  }

  setToken(token) {
    this.token = token;
    if (token) {
      localStorage.setItem('ns_token', token);
    } else {
      localStorage.removeItem('ns_token');
    }
  }

  async request(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    const res = await fetch(`${API_BASE}${path}`, { ...options, headers });
    if (res.status === 401) {
      this.setToken(null);
      window.location.href = '/login';
      throw new Error('Unauthorized');
    }
    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || 'Request failed');
    }
    return res.json();
  }

  get(path) { return this.request(path); }
  post(path, body) { return this.request(path, { method: 'POST', body: JSON.stringify(body) }); }
  del(path) { return this.request(path, { method: 'DELETE' }); }

  // Auth
  login(username, password) { return this.post('/auth/login', { username, password }); }
  classCodeLogin(classCode, studentId) { return this.post('/auth/class-code-login', { class_code: classCode, student_identifier: studentId }); }
  register(data) { return this.post('/auth/register', data); }
  getMe() { return this.get('/auth/me'); }

  // Classrooms
  listClassrooms() { return this.get('/classrooms'); }
  createClassroom(name) { return this.post('/classrooms', { name }); }
  getClassroom(id) { return this.get(`/classrooms/${id}`); }
  deleteClassroom(id) { return this.del(`/classrooms/${id}`); }
  listStudents(classroomId) { return this.get(`/classrooms/${classroomId}/students`); }
  enrollStudent(classroomId, data) { return this.post(`/classrooms/${classroomId}/students`, data); }
  removeStudent(classroomId, studentId) { return this.del(`/classrooms/${classroomId}/students/${studentId}`); }

  // Skills
  listSkills(domain) { return this.get(`/skills${domain ? `?domain=${domain}` : ''}`); }
  listDomains() { return this.get('/skills/domains'); }

  // Assignments
  createAssignment(data) { return this.post('/assignments', data); }
  listAssignments(classroomId) { return this.get(`/assignments/classroom/${classroomId}`); }
  myAssignments() { return this.get('/assignments/my'); }
  deleteAssignment(id) { return this.del(`/assignments/${id}`); }

  // Practice
  startSession(assignmentId) { return this.post('/practice/start', { assignment_id: assignmentId }); }
  getNextProblem(sessionId) { return this.get(`/practice/problem/${sessionId}`); }
  submitAnswer(data) { return this.post('/practice/answer', data); }
  getSessionSummary(sessionId) { return this.get(`/practice/session/${sessionId}/summary`); }

  // Analytics
  classroomOverview(classroomId) { return this.get(`/analytics/classroom/${classroomId}/overview`); }
  studentProgress(studentId, classroomId) { return this.get(`/analytics/student/${studentId}/progress?classroom_id=${classroomId}`); }

  // Google Classroom
  googleStatus() { return this.get('/google/status'); }
  googleOAuthUrl() { return this.get('/google/oauth/url'); }
  googleOAuthCallback(code) { return this.post('/google/oauth/callback', { code }); }
  googleDisconnect() { return this.post('/google/disconnect', {}); }
  googleListCourses() { return this.get('/google/classroom/courses'); }
  googleImportCourses() { return this.post('/google/classroom/import-courses', {}); }
  googlePostAssignment(data) { return this.post('/google/classroom/post-assignment', data); }
  googleAssignmentLinks(assignmentId) { return this.get(`/google/classroom/assignment-links/${assignmentId}`); }
}

const api = new ApiService();
export default api;
