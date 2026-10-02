const loginForm = document.querySelector('#login-form');
const taskForm = document.querySelector('#task-form');
const taskList = document.querySelector('#task-list');
const categorySelect = document.querySelector('#category-select');
const message = document.querySelector('#message');
const connectionState = document.querySelector('#connection-state');
const refreshButton = document.querySelector('#refresh-button');

let accessToken = null;
let gatewayBaseUrl = '';
let taskLinks = null;
let categoriesById = new Map();

function setMessage(text, isError = false) {
  message.textContent = text;
  message.classList.toggle('error', isError);
}

function resolveGatewayLink(link) {
  if (!link?.href) throw new Error('O Gateway não retornou o link HATEOAS esperado.');
  return new URL(link.href, `${gatewayBaseUrl}/`).toString();
}

async function gatewayRequest(link, options = {}) {
  const response = await fetch(resolveGatewayLink(link), {
    ...options,
    headers: {
      ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      ...(options.body ? { 'Content-Type': 'application/json' } : {}),
      ...options.headers,
    },
  });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.detail || `Falha na requisição (${response.status}).`);
  return body;
}

function renderTasks(tasks) {
  taskList.replaceChildren();
  if (!tasks.length) {
    setMessage('Ainda não há tarefas. Crie a primeira acima.');
    return;
  }
  setMessage(`${tasks.length} tarefa${tasks.length === 1 ? '' : 's'} na lista.`);
  for (const task of tasks) {
    const item = document.createElement('li');
    item.className = 'task-item';
    const title = document.createElement('span');
    title.className = 'task-name';
    title.textContent = task.title;
    const category = document.createElement('span');
    category.className = 'task-category';
    category.textContent = categoriesById.get(task.category_id) || task.category_id;
    item.append(title, category);
    taskList.append(item);
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

loginForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const gatewayInput = document.querySelector('#gateway-url').value.trim().replace(/\/$/, '');
  gatewayBaseUrl = gatewayInput;
  setMessage('Autenticando e carregando dados...');
  try {
    const tokenResult = await gatewayRequest({ href: '/auth/demo-token', method: 'POST' }, {
      body: JSON.stringify({
        username: document.querySelector('#username').value,
        password: document.querySelector('#password').value,
      }),
    });
    accessToken = tokenResult.access_token;
    await loadCategories(tokenResult._links.categories);
    await loadTasks();
    connectionState.textContent = 'Conectado';
    connectionState.classList.add('connected');
    refreshButton.disabled = false;
    taskForm.querySelector('button').disabled = false;
  } catch (error) {
    accessToken = null;
    connectionState.textContent = 'Desconectado';
    connectionState.classList.remove('connected');
    setMessage(error.message, true);
  }
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
