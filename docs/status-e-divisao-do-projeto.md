# Status, pendências e divisão do projeto

Este documento resume o que já existe no repositório, o que ainda precisa ser concluído e como o trabalho pode ser dividido sem bloquear os integrantes. Ele complementa o [contrato das APIs](contrato-api.md), que define rotas e formatos de dados para a integração.

## 1. Visão geral

O projeto é uma aplicação de lista de tarefas com categorias, organizada em quatro partes:

1. **Cliente Web:** interface usada pela pessoa que acessa o sistema.
2. **Gateway REST:** único ponto de entrada do cliente; valida JWT e encaminha pedidos.
3. **API de tarefas:** cria e consulta tarefas.
4. **API de categorias:** fornece as categorias disponíveis.

Fluxo esperado:

```text
Pessoa usuária → Cliente Web → Gateway (JWT e HATEOAS) → API de tarefas / API de categorias
```

O cliente web deve chamar somente o Gateway. As APIs de tarefas e categorias são serviços internos e não devem ser acessadas diretamente pelo navegador.

## 2. O que já foi feito

- Criada a estrutura inicial para Gateway, dois serviços, cliente web e documentação.
- **Gateway:** há rotas para emissão de token de demonstração, consulta/criação de tarefas e consulta de categorias. As rotas de dados exigem JWT; as respostas incluem links HATEOAS. Também há tratamento básico de indisponibilidade de serviço e documentação Swagger automática.
- **API de tarefas:** há uma implementação inicial em memória para listar, consultar por ID e criar tarefas.
- **API de categorias:** há uma implementação inicial em memória com categorias de exemplo.
- **Cliente Web:** há uma interface inicial para autenticar, carregar categorias, criar tarefa e atualizar a lista.
- Criado um arquivo de exemplo de variáveis de ambiente, dependências Python e instruções de execução no README.
- Definido um contrato inicial com endereços, rotas e formatos de dados em [contrato-api.md](contrato-api.md).

**Importante:** existe uma base funcional para desenvolvimento, mas isso não significa que o fluxo completo já esteja validado nas máquinas do grupo ou do laboratório. Os dados das APIs são temporários e são apagados quando os processos são reiniciados.

## 3. Divisão de tarefas

| Pessoa / parte                  | Responsabilidade                                                                                     | De quem depende                                                                                                                                     | O que precisa combinar ou receber                                                                                                                                                            |
| ------------------------------- | ---------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Bruno — Gateway**             | Autenticação JWT, encaminhamento às APIs, tratamento de erros, HATEOAS e documentação do Gateway.    | Para integrar de verdade, depende das rotas e respostas das APIs de tarefas e categorias. Pode desenvolver contra o contrato enquanto elas evoluem. | Confirmar que os endereços/portas permanecem os do contrato; combinar mudanças de rotas ou formatos antes de fazê-las; receber aviso quando cada serviço estiver disponível para integração. |
| **Patricia — API de tarefas**   | Criar, listar e consultar tarefas; validar os dados recebidos.                                       | Precisa dos IDs estáveis das categorias definidos por Gustavo. Para o desenvolvimento inicial, pode usar os IDs de exemplo do contrato.             | Combinar com Gustavo os IDs; manter `category_id` como texto e usar os formatos e códigos HTTP documentados; avisar Bruno quando a API estiver pronta.                                       |
| **Gustavo — API de categorias** | Manter a lista de categorias e disponibilizá-la pela API.                                            | Quase independente; precisa combinar os IDs com Patricia e informar os IDs usados ao restante do grupo.                                             | Definir com Patricia IDs fixos, como `estudo`, `trabalho` e `pessoal`; manter o formato `{ "id": "...", "name": "..." }`; avisar Bruno quando a rota estiver pronta.                         |
| **Todos — Cliente Web**         | Construir e testar a interface para autenticar, listar tarefas, selecionar categoria e criar tarefa. | Para o fluxo completo, depende do contrato do Gateway; para testar ponta a ponta, precisa do Gateway e das duas APIs em execução.                   | Chamar somente o Gateway; usar o JWT retornado no cabeçalho Bearer; seguir os links `_links` recebidos; combinar alterações visuais e de integração para evitar sobrescrever trabalho.       |

## 4. O que cada pessoa deve fazer

### Bruno — Gateway

- [ ] Conferir no Swagger (`/docs`) as rotas de autenticação, tarefas e categorias.
- [ ] Testar acesso às rotas protegidas sem token, com token inválido e com token válido.
- [ ] Testar criação, listagem e consulta de tarefa usando as APIs reais, e não apenas respostas simuladas.
- [ ] Conferir os links HATEOAS e garantir que o cliente consiga navegar usando esses links.
- [ ] Testar e documentar o erro retornado quando uma API interna estiver indisponível.
- [ ] Configurar endereços e CORS para a demonstração em rede, se cliente e servidor estiverem em máquinas diferentes.
- [ ] Explicar na apresentação o papel do Gateway e como ele esconde as APIs internas do cliente.

### Patricia — API de tarefas

- [ ] Confirmar que `GET /tasks`, `GET /tasks/{id}` e `POST /tasks` seguem o contrato.
- [ ] Garantir que a tarefa contenha `id`, `title`, `category_id` e `completed`.
- [ ] Validar título e categoria recebidos e retornar erros HTTP apropriados para dados inválidos ou tarefa inexistente.
- [ ] Combinar e usar os IDs de categorias definidos com Gustavo.
- [ ] Testar a documentação automática da API em `/docs` e os casos de sucesso e erro.
- [ ] Informar Bruno quando o serviço estiver pronto e disponível no endereço acordado.

### Gustavo — API de categorias

- [ ] Confirmar com Patricia a lista e os IDs permanentes das categorias.
- [ ] Manter `GET /categories` retornando itens no formato `{ "id": "...", "name": "..." }`.
- [ ] Manter o endpoint de verificação `GET /health`.
- [ ] Testar a API e sua documentação em `/docs`.
- [ ] Informar Patricia, Bruno e quem trabalha no cliente quando os IDs estiverem definidos e quando a API estiver pronta.

### Todos — Cliente Web e integração

- [ ] Confirmar que a tela obtém o token antes de chamar rotas protegidas.
- [ ] Conferir que as chamadas usam `Authorization: Bearer <token>`.
- [ ] Carregar categorias do Gateway e permitir selecioná-las ao criar uma tarefa.
- [ ] Exibir tarefas, mensagens de carregamento, lista vazia e erros de conexão/autenticação.
- [ ] Seguir os links HATEOAS recebidos do Gateway, sem usar endereços internos dos microserviços.
- [ ] Testar o navegador com todos os processos iniciados simultaneamente.
- [ ] Escolher quem fica responsável por cada ajuste visual ou funcional do cliente e integrar as mudanças por Git.

## 5. Dependências principais e ordem de integração

1. **Gustavo e Patricia definem os IDs de categoria.** Os IDs precisam ser estáveis para que `category_id` da tarefa corresponda a uma categoria existente.
2. **Patricia e Gustavo implementam suas APIs em paralelo**, seguindo o contrato. Bruno pode continuar o Gateway usando as rotas já especificadas.
3. **Bruno conecta e testa as APIs reais no Gateway.** Se um contrato precisar mudar, os três envolvidos devem combinar a mudança e atualizar a documentação.
4. **O cliente integra com o Gateway.** A interface pode ser desenvolvida antes, mas o teste completo só acontece quando Gateway e serviços estiverem disponíveis.
5. **Todos fazem o teste ponta a ponta** em um ambiente comum e corrigem problemas de endereço, porta, CORS, JWT ou formato de resposta.

### Regra para alterações no contrato

Não trocar nomes de campos, IDs, rotas, portas ou formatos unilateralmente. Se uma alteração for necessária, avisar as pessoas afetadas, atualizar [contrato-api.md](contrato-api.md) e só então adaptar as implementações.

## 6. Pendências do grupo antes da entrega

- [ ] Confirmar se as APIs continuam usando dados em memória ou se o grupo implementará persistência (por exemplo, SQLite). Persistência não é requisito explícito na divisão atual, mas sem ela os dados somem ao reiniciar os serviços.
- [ ] Testar todas as rotas usando os serviços reais, além de validar os componentes separadamente.
- [ ] Confirmar a configuração final de endereços, portas e CORS para a rede do laboratório. `127.0.0.1` aponta para a própria máquina e não serve como endereço de servidor para outro computador.
- [ ] Definir como iniciar os componentes no laboratório e verificar que o cliente da máquina principal alcança o servidor.
- [ ] Criar/publicar o repositório no GitHub e compartilhar o link com o professor e o grupo.
- [ ] Garantir que arquivos secretos locais (`.env`) não sejam enviados ao GitHub; publicar somente o `.env.example` sem segredos reais.
- [ ] Ensaiar a apresentação e permitir que outra pessoa teste o fluxo sem depender de explicações do desenvolvedor.

## 7. Roteiro sugerido para validar a demonstração

1. Iniciar API de tarefas, API de categorias, Gateway e servidor do cliente web.
2. Abrir o cliente web e conectar usando as credenciais de demonstração configuradas localmente.
3. Mostrar que categorias e tarefas são carregadas através do Gateway.
4. Criar uma tarefa escolhendo uma categoria e confirmar que aparece na lista.
5. Abrir o Swagger do Gateway e demonstrar as rotas documentadas.
6. Mostrar que uma chamada sem JWT é recusada e explicar que o JWT é enviado pelo cliente.
7. Explicar o uso dos links HATEOAS e as responsabilidades separadas dos dois microserviços.
8. Opcionalmente, desligar um serviço para demonstrar a mensagem de indisponibilidade do Gateway.

## 8. Observações sobre a autenticação atual

A autenticação existente é simplificada para demonstração: um usuário e uma senha configurados por ambiente permitem emitir um JWT. As credenciais padrão são apenas exemplos locais, não representam cadastro de usuários nem devem ser usadas em produção. Antes da apresentação, o grupo deve configurar o segredo e as credenciais locais conforme combinado, sem publicar segredos reais no repositório.
