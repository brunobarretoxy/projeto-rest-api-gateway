const loginForm = document.querySelector('#login-form');
const taskForm = document.querySelector('#task-form');
const taskList = document.querySelector('#task-list');
const categorySelect = document.querySelector('#category-select');
const taskMessage = document.querySelector('#task-message');
const listSummary = document.querySelector('#list-summary');
const taskFilters = document.querySelector('#task-filters');
const progressCount = document.querySelector('#progress-count');
const progressFill = document.querySelector('#progress-fill');
const progressTrack = document.querySelector('.progress-track');
const filterButtons = [...document.querySelectorAll('.filter-chip')];
const authMessage = document.querySelector('#message');
const connectionState = document.querySelector('#connection-state');
const refreshButton = document.querySelector('#refresh-button');
const logoutButton = document.querySelector('#logout-button');
const sessionIndicator = document.querySelector('#session-indicator');
const themeToggle = document.querySelector('#theme-toggle');
const authView = document.querySelector('#auth-view');
const tasksView = document.querySelector('#tasks-view');
const accountSwitchButton = document.querySelector('#account-switch-button');
const loginTab = document.querySelector('#login-tab');
const accountHint = document.querySelector('#account-hint');
const loginTitle = document.querySelector('#login-title');
const passwordInput = document.querySelector('#password');
const usernameInput = document.querySelector('#username');
const emailField = document.querySelector('#email-field');
const emailInput = document.querySelector('#email');
const authSubmit = document.querySelector('#auth-submit');

let accessToken = null;
let isRegisterMode = new URLSearchParams(window.location.search).get('mode') === 'register';
let gatewayBaseUrl = window.APP_CONFIG?.gatewayBaseUrl
  || `${window.location.protocol}//${window.location.hostname}:8000`;
let taskLinks = null;
let categoriesById = new Map();
let currentTasks = [];
let activeFilter = 'all';

function applyTheme(theme) {
  const isDark = theme === 'dark';
  document.documentElement.dataset.theme = isDark ? 'dark' : 'light';
  themeToggle.setAttribute('aria-label', isDark ? 'Ativar tema claro' : 'Ativar tema escuro');
  themeToggle.innerHTML = isDark
    ? '<span class="theme-toggle-icon" aria-hidden="true">☀</span><span class="theme-toggle-label">Tema claro</span>'
    : '<span class="theme-toggle-icon" aria-hidden="true">☾</span><span class="theme-toggle-label">Tema escuro</span>';
  localStorage.setItem('parea-organizae-theme', isDark ? 'dark' : 'light');
}

applyTheme(localStorage.getItem('parea-organizae-theme') || localStorage.getItem('dia-a-dia-theme') || 'light');
themeToggle.addEventListener('click', () => {
  applyTheme(document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark');
});

function setMessage(text, isError = false) {
  taskMessage.textContent = text;
  taskMessage.classList.toggle('error', isError);
}

function showLoginForm() {
  authView.hidden = false;
  tasksView.hidden = true;
  sessionIndicator.hidden = true;
  loginTab.classList.toggle('active', !isRegisterMode);
  loginTab.setAttribute('aria-selected', String(!isRegisterMode));
  accountSwitchButton.classList.toggle('active', isRegisterMode);
  accountSwitchButton.setAttribute('aria-selected', String(isRegisterMode));
  loginTitle.textContent = isRegisterMode ? 'Crie sua conta' : 'Acesse suas tarefas';
  authSubmit.textContent = isRegisterMode ? 'Criar conta e entrar' : 'Entrar';
  emailField.hidden = !isRegisterMode;
  emailInput.required = isRegisterMode;
  accountHint.textContent = isRegisterMode
    ? 'Informe seu e-mail, escolha um usuário e uma senha segura.'
    : 'Entre para organizar suas tarefas por categoria.';
}

function resolveGatewayLink(link) {
  if (!link?.href) throw new Error('O Gateway não retornou o link HATEOAS esperado.');
  return new URL(link.href, `${gatewayBaseUrl}/`).toString();
}

async function gatewayRequest(link, options = {}) {
  let response;
  try {
    response = await fetch(resolveGatewayLink(link), {
      ...options,
      method: options.method || link.method || 'GET',
      headers: {
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
        ...(options.body ? { 'Content-Type': 'application/json' } : {}),
        ...options.headers,
      },
    });
  } catch {
    throw new Error('Não foi possível conectar ao serviço. Verifique se o sistema está em execução.');
  }
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    const detail = typeof body.detail === 'string'
      ? body.detail
      : body.detail?.password?.[0]
        || body.detail?.username?.[0]
        || body.detail?.category_id?.[0]
        || body.detail?.email?.[0]
        || body.detail?.title?.[0]
        || 'Confira os dados e tente novamente.';
    throw new Error(detail || `Falha na requisição (${response.status}).`);
  }
  return body;
}

function renderTasks(tasks) {
  currentTasks = tasks;
  taskList.replaceChildren();
  taskFilters.hidden = tasks.length === 0;
  listSummary.hidden = tasks.length === 0;
  const completedCount = tasks.filter((task) => task.completed).length;
  const pendingCount = tasks.length - completedCount;
  const percent = tasks.length ? Math.round((completedCount / tasks.length) * 100) : 0;
  document.querySelector('#all-count').textContent = tasks.length;
  document.querySelector('#pending-count').textContent = pendingCount;
  document.querySelector('#completed-count').textContent = completedCount;
  progressCount.textContent = `${completedCount} de ${tasks.length} feitas`;
  progressFill.style.width = `${percent}%`;
  progressTrack.setAttribute('aria-valuenow', String(percent));

  const filteredTasks = tasks.filter((task) => {
    if (activeFilter === 'pending') return !task.completed;
    if (activeFilter === 'completed') return task.completed;
    return true;
  });

  if (!filteredTasks.length && tasks.length) {
    const empty = document.createElement('li');
    empty.className = 'filtered-empty';
    empty.textContent = activeFilter === 'completed'
      ? 'Ainda não tem nenhuma tarefa feita. Um pequeno passo já conta.'
      : 'Tudo em dia! Você concluiu todas as tarefas.';
    taskList.append(empty);
    setMessage('');
    return;
  }
  if (!tasks.length) {
    setMessage('Ainda não há tarefas. Crie a primeira acima.');
    return;
  }
  setMessage(`${filteredTasks.length} ${activeFilter === 'completed' ? 'concluída' : activeFilter === 'pending' ? 'pendente' : 'tarefa'}${filteredTasks.length === 1 ? '' : 's'}`);
  for (const task of filteredTasks) {
    const item = document.createElement('li');
    item.className = `task-item${task.completed ? ' is-completed' : ''}`;
    const toggle = document.createElement('button');
    toggle.className = 'task-check';
    toggle.type = 'button';
    toggle.setAttribute('aria-label', task.completed ? `Reabrir ${task.title}` : `Concluir ${task.title}`);
    toggle.setAttribute('aria-pressed', String(Boolean(task.completed)));
    toggle.textContent = task.completed ? '✓' : '';
    toggle.addEventListener('click', () => toggleTask(task));
    const title = document.createElement('span');
    title.className = 'task-name';
    title.textContent = task.title;
    const category = document.createElement('span');
    category.className = 'task-category';
    category.textContent = categoriesById.get(task.category_id) || task.category_id;
    const content = document.createElement('div');
    content.className = 'task-content';
    content.append(title, category);
    item.append(toggle, content);
    taskList.append(item);
  }
}

async function toggleTask(task) {
  const completionLink = task._links?.completion;
  if (!completionLink) {
    setMessage('Não encontrei o link para atualizar esta tarefa.', true);
    return;
  }
  try {
    await gatewayRequest(completionLink, {
      body: JSON.stringify({ completed: !task.completed }),
    });
    await loadTasks();
  } catch (error) {
    setMessage(error.message, true);
  }
}

async function loadTasks() {
  if (!taskLinks) return;
  setMessage('Carregando tarefas...');
  const result = await gatewayRequest(taskLinks.self);
  taskLinks = result._links;
  renderTasks(result.data);
}

async function loadCategories(link) {
  const result = await gatewayRequest(link);
  categoriesById = new Map(result.data.map((category) => [category.id, category.name]));
  categorySelect.replaceChildren(new Option('Selecione uma categoria', ''));
  for (const category of result.data) {
    categorySelect.add(new Option(category.name, category.id));
  }
}

filterButtons.forEach((button) => {
  button.addEventListener('click', () => {
    activeFilter = button.dataset.filter;
    filterButtons.forEach((filter) => filter.classList.toggle('active', filter === button));
    renderTasks(currentTasks);
  });
});

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const submitButton = loginForm.querySelector('button[type="submit"]');
  submitButton.disabled = true;
  authMessage.textContent = 'Verificando seus dados...';
  authMessage.classList.remove('error');
  try {
    const tokenResult = await gatewayRequest({
      href: isRegisterMode ? '/auth/register' : '/auth/token',
      method: 'POST',
    }, {
      body: JSON.stringify({
        username: document.querySelector('#username').value,
        password: passwordInput.value,
        ...(isRegisterMode ? { email: emailInput.value.trim() } : {}),
      }),
    });
    accessToken = tokenResult.access_token;
    taskLinks = { self: tokenResult._links.tasks };
    await loadCategories(tokenResult._links.categories);
    await loadTasks();
    authMessage.textContent = '';
    authMessage.classList.remove('error');
    connectionState.textContent = 'Conectado';
    authView.hidden = true;
    tasksView.hidden = false;
    sessionIndicator.hidden = false;
    refreshButton.disabled = false;
    taskForm.querySelector('button').disabled = false;
  } catch (error) {
    accessToken = null;
    taskLinks = null;
    taskList.replaceChildren();
    showLoginForm();
    refreshButton.disabled = true;
    taskForm.querySelector('button').disabled = true;
    authMessage.textContent = error.message;
    authMessage.classList.add('error');
  } finally {
    submitButton.disabled = false;
  }
});

logoutButton.addEventListener('click', () => {
  accessToken = null;
  taskLinks = null;
  taskList.replaceChildren();
  categorySelect.replaceChildren(new Option('Entre para carregar as categorias', ''));
  isRegisterMode = false;
  window.history.replaceState(null, '', window.location.pathname);
  showLoginForm();
  loginForm.reset();
  passwordInput.autocomplete = 'current-password';
  passwordInput.minLength = 8;
  authMessage.textContent = 'Você saiu da sua conta.';
  authMessage.classList.remove('error');
  refreshButton.disabled = true;
  taskForm.querySelector('button').disabled = true;
});

taskForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  if (!taskLinks?.create) return;
  const submitButton = taskForm.querySelector('button');
  submitButton.disabled = true;
  try {
    await gatewayRequest(taskLinks.create, {
      body: JSON.stringify({
        title: document.querySelector('#task-name').value.trim(),
        category_id: categorySelect.value,
      }),
    });
    taskForm.reset();
    activeFilter = 'all';
    filterButtons.forEach((filter) => filter.classList.toggle('active', filter.dataset.filter === 'all'));
    await loadTasks();
  } catch (error) {
    setMessage(error.message, true);
  } finally {
    submitButton.disabled = false;
  }
});

refreshButton.addEventListener('click', async () => {
  try {
    await loadTasks();
  } catch (error) {
    setMessage(error.message, true);
  }
});

taskForm.querySelector('button').disabled = true;

if (isRegisterMode) {
  passwordInput.autocomplete = 'new-password';
  showLoginForm();
}
