# Organizaê Parêa — guia de apresentação e defesa

Este guia ajuda a preparar uma explicação clara do projeto, demonstrar seu funcionamento e responder perguntas. O texto descreve o comportamento implementado no repositório; se uma alteração recente mudar o código, use o código e o contrato em [`contrato-api.md`](contrato-api.md) como fontes de verdade.

## 1. O projeto em poucas palavras

O **Organizaê Parêa** é um organizador pessoal de tarefas por categoria. A pessoa cria uma conta, entra, consulta as próprias tarefas, escolhe uma categoria ao criar uma tarefa e pode marcá-la como concluída ou reabri-la.

O trabalho também demonstra uma arquitetura distribuída simples: um Cliente Web chama um API Gateway; o Gateway autentica as requisições e encaminha chamadas para dois serviços independentes — tarefas e categorias.

### Apresentação de 20 segundos

> “O Organizaê Parêa organiza tarefas pessoais por categoria. A interface web acessa somente o Gateway, que emite e valida JWT, encaminha os pedidos para a API de tarefas ou de categorias e devolve links HATEOAS. As tarefas ficam associadas à conta autenticada.”

## 2. A arquitetura e o caminho de uma requisição

```text
Navegador
  │ HTML/CSS/JavaScript
  ▼
Cliente Web :5500
  │ HTTP + JWT (Bearer)
  ▼
Gateway FastAPI :8000
  ├── HTTP + X-User-Id ──► API de tarefas Django REST :8001 ──► SQLite
  └── HTTP ──────────────► API de categorias FastAPI :8002
```

- **Cliente Web:** exibe a interface; não acessa diretamente as APIs internas.
- **Gateway:** ponto de entrada público. Faz cadastro/login, emite e valida JWT, encaminha as chamadas, padroniza parte das respostas e cria links HATEOAS.
- **API de tarefas:** cria, lista, consulta e altera o estado concluído das tarefas. Persiste os registros em SQLite e filtra pelo proprietário recebido do Gateway.
- **API de categorias:** disponibiliza a lista estável de categorias.

As portas diferentes permitem executar esses processos na mesma máquina durante o desenvolvimento. As pastas organizam o código; é o fato de cada serviço ser executado como processo/servidor separado que estabelece a separação de execução.

## 3. Conceitos que o professor pode perguntar

### API REST

Uma API é um contrato de comunicação. Ela define rotas, métodos HTTP, dados de entrada, respostas e erros. Por exemplo, `POST /tasks` cria uma tarefa e `GET /tasks` lista tarefas. REST usa recursos, métodos HTTP e códigos de status de maneira previsível.

**Por que há duas APIs internas?** Para separar responsabilidades: uma gerencia tarefas, a outra fornece categorias. Podem ser executadas e testadas separadamente, enquanto seguem contratos combinados.

### API Gateway

É a entrada do sistema para o Cliente Web. O navegador não precisa conhecer o endereço de cada microserviço: chama o Gateway, que verifica o JWT e encaminha o pedido correto. Isso centraliza autenticação e roteamento e evita expor os serviços internos diretamente ao cliente.

### JWT

JWT é um token assinado que representa uma identidade e tem validade. Após cadastro ou login, o Gateway emite o token. O navegador o envia como `Authorization: Bearer <token>`; o Gateway verifica assinatura e expiração antes de autorizar as rotas protegidas.

No projeto, a assinatura usa `JWT_SECRET`. O token contém o nome de usuário no `sub` e um prazo de expiração. A senha não vai dentro do token.

### HATEOAS

HATEOAS significa que uma resposta REST inclui links para recursos ou ações relacionados. Por exemplo, uma tarefa retorna seu link `self` e o link `completion`, cujo método é `PATCH`. O cliente usa os links recebidos em vez de construir o endereço do serviço interno.

### CORS

CORS é uma regra aplicada pelo navegador quando a página e a API estão em origens diferentes — por exemplo, porta 5500 para 8000. O Gateway precisa autorizar a origem do Cliente Web. CORS não é autenticação nem firewall; apenas controla quais páginas web podem ler respostas do Gateway.

### Persistência e isolamento

- **Contas:** SQLite local do Gateway; as senhas são derivadas com scrypt e sal, não armazenadas em texto puro.
- **Tarefas:** SQLite do serviço Django. A identidade validada pelo Gateway é encaminhada como `X-User-Id`; a API filtra tarefas por esse proprietário.
- **Categorias:** lista fixa no código do serviço de categorias.

A API de tarefas e a de categorias não dependem uma da disponibilidade de rede da outra. Elas dependem do contrato: os IDs de categoria aceitos pelas tarefas devem coincidir com os IDs publicados pelo serviço de categorias.

## 4. Fluxos para explicar no quadro

### Cadastro e primeiro acesso

1. A pessoa envia usuário, e-mail e senha para `POST /auth/register` no Gateway.
2. O Gateway valida os campos, normaliza usuário/e-mail e rejeita duplicatas.
3. O serviço de contas armazena a senha como hash scrypt no SQLite.
4. O Gateway emite um JWT e responde com links de tarefas, categorias e perfil.
5. O Cliente Web usa o token para carregar tarefas e categorias.

### Login

1. O Cliente Web envia usuário e senha a `POST /auth/token`.
2. O Gateway verifica a senha contra o hash armazenado.
3. Se correta, emite JWT. Se incorreta, responde HTTP 401.

### Criar uma tarefa

1. O navegador envia `POST /api/tasks` ao Gateway com o JWT e JSON `{ "title": "Estudar REST", "category_id": "estudo" }`.
2. O Gateway valida o JWT e encaminha o pedido para `POST /tasks` no serviço Django, adicionando a identidade interna do usuário.
3. O serviço verifica título/categoria, grava a tarefa no SQLite e responde HTTP 201.
4. O Gateway acrescenta links HATEOAS; o Cliente Web atualiza a lista.

### Concluir ou reabrir uma tarefa

1. A tarefa na resposta possui um link HATEOAS `completion` com método `PATCH`.
2. O Cliente Web segue esse link e envia `{ "completed": true }` ou `false`, com JWT.
3. O Gateway valida identidade e encaminha o pedido à API de tarefas.
4. O serviço só altera uma tarefa que pertença à conta autenticada.
5. O Cliente Web atualiza os contadores, o progresso e o filtro visível.

### Quando um microserviço está fora do ar

Se o Gateway não consegue conectar-se ao serviço interno, retorna HTTP 503 com uma mensagem de indisponibilidade. O Gateway continua sendo o endereço conhecido pelo cliente; ele não deve ser configurado para chamar o microserviço diretamente.

## 5. Roteiro sugerido para a apresentação

Planejem cerca de 6–8 minutos e deixem os quatro processos iniciados antes de começar.

1. **Problema e objetivo (30 s):** explicar que o sistema organiza tarefas pessoais por categoria.
2. **Arquitetura (1 min):** mostrar o diagrama e dizer por que o navegador chama o Gateway, não as APIs internas.
3. **Cadastro/login (1 min):** criar uma conta de demonstração ou entrar em uma conta já preparada. Não mostrar senhas reais.
4. **Uso do site (1–2 min):** mostrar categorias, criar tarefa, usar filtros, concluir/reabrir e observar progresso.
5. **JWT e documentação (1 min):** abrir `http://<IP-DO-SERVIDOR>:8000/docs`, mostrar `/auth/token`, `Authorize` e uma rota protegida. Uma chamada sem token retorna 401.
6. **HATEOAS (1 min):** mostrar na resposta de tarefa os links `self` e `completion`, além dos links de coleção.
7. **Microserviços (1 min):** mostrar Swagger de tarefas e categorias e explicar o papel de cada API.
8. **Robustez (opcional):** parar um serviço interno e demonstrar a resposta 503 do Gateway.
9. **Encerramento:** resumir as tecnologias, persistência e responsabilidades separadas.

Para a sala, faça o ensaio no mesmo Wi-Fi: veja o IP com `ipconfig`, configure `.env` e `web/config.js`, inicie Gateway e Cliente Web com bind `0.0.0.0`, libere as portas 8000/5500 no firewall privado e abra `http://<IP-DO-SERVIDOR>:5500` no computador cliente. Use o guia [`execucao-e-apresentacao.md`](execucao-e-apresentacao.md) para os comandos completos.

## 6. Perguntas prováveis e respostas curtas

### Perguntas prioritárias: Gateway e APIs

Estas são as perguntas mais diretamente ligadas ao foco do trabalho. Vale praticar estas respostas primeiro.

#### “Qual é exatamente a responsabilidade do Gateway neste projeto?”

> “É o ponto de entrada das chamadas do Cliente Web. O Gateway oferece cadastro/login, emite e valida JWT, encaminha operações para a API de tarefas ou de categorias, converte falhas de conexão em HTTP 503 e acrescenta links HATEOAS. O navegador não precisa saber os endereços internos dos microserviços.”

#### “O Gateway é só um proxy?”

> “Ele encaminha as requisições, mas também aplica responsabilidades próprias: autenticação e autorização JWT, validação de algumas entradas públicas, tradução de indisponibilidade e composição de respostas com HATEOAS. Por isso funciona como uma camada de API Gateway, não apenas como encaminhador transparente.”

#### “Descreva uma chamada do começo ao fim.”

> “O navegador manda uma requisição HTTP ao Gateway com o JWT Bearer. O Gateway valida assinatura e expiração, identifica o usuário no `sub` e chama o microserviço correspondente. Na API de tarefas, encaminha também a identidade interna do usuário. O serviço processa a operação e responde; o Gateway devolve os dados e links ao Cliente Web.”

#### “Que operações o Gateway publica e para que serve cada método?”

> “`POST /auth/register` cria conta e emite token; `POST /auth/token` autentica e emite token. Com token, `GET /api/tasks` lista, `POST /api/tasks` cria, `GET /api/tasks/{id}` consulta e `PATCH /api/tasks/{id}` altera o estado concluído. `GET /api/categories` lista categorias. GET consulta, POST cria e PATCH altera parcialmente um recurso.”

#### “Quais são as APIs internas e por que são separadas?”

> “A API de tarefas é um serviço Django REST Framework que gerencia e persiste tarefas. A API de categorias é um serviço FastAPI que publica a lista de categorias. Têm processos e contratos próprios, podem ser iniciadas/testadas separadamente e o Gateway as integra por HTTP.”

#### “É aceitável os microserviços usarem frameworks diferentes?”

> “Sim. O protocolo entre eles é HTTP, então o Gateway não depende de Django ou FastAPI: depende das rotas, dos métodos, dos campos JSON e dos códigos HTTP acordados. O contrato comum é o que permite a interoperabilidade.”

#### “O que autentica cada chamada e como o Gateway sabe de quem é a tarefa?”

> “O cliente envia um JWT assinado no cabeçalho Bearer. O Gateway valida o token e usa o `sub` verificado como identidade. Nas chamadas internas de tarefas, envia essa identidade em `X-User-Id`; a API filtra consulta, alteração e criação pelo proprietário. A interface não escolhe esse identificador.”

#### “Por que `X-User-Id` é enviado em vez de o microserviço validar o JWT?”

> “Neste protótipo, a validação JWT foi centralizada no Gateway, que encaminha a identidade já verificada. Isso simplifica a demonstração do Gateway. Por isso a API de tarefas deve ficar restrita à rede interna; se fosse exposta diretamente, seria necessário autenticar também a comunicação entre serviços ou validar o token nela.”

#### “Os microserviços funcionam separadamente se compartilham IDs de categoria?”

> “Sim. A API de tarefas não faz chamada de rede à API de categorias para cada operação. Ela valida `category_id` contra os IDs estáveis acordados. É dependência do contrato de dados, não dependência de disponibilidade. Se os IDs mudarem, as duas implementações e a documentação precisam ser atualizadas juntas.”

#### “Como o Gateway reage a respostas e falhas dos serviços?”

> “Respostas HTTP de erro do microserviço são repassadas com seu status e detalhe quando possível. Se não houver conexão com o serviço, o Gateway responde HTTP 503. Assim o cliente fala com uma interface pública consistente e não precisa conhecer a topologia interna.”

#### “Onde a documentação e o contrato podem ser verificados?”

> “O FastAPI expõe Swagger em `/docs` para o Gateway e a API de categorias; a API Django usa drf-spectacular e também expõe `/docs`. O contrato compartilhado está em `docs/contrato-api.md`. Swagger mostra operações e formatos; o contrato explica como os componentes concordam em integrá-las.”

#### “Como demonstrar que o JWT realmente protege o Gateway?”

> “No Swagger, chamar uma rota protegida sem token e observar HTTP 401. Depois autenticar em `/auth/token`, copiar o JWT para `Authorize` como Bearer e repetir a chamada: com token válido, o Gateway prossegue; com token inválido ou expirado, volta a responder 401.”

#### “O que o HATEOAS acrescenta especificamente ao Gateway?”

> “O Gateway coloca links nas respostas: `self` para consultar o recurso, `completion` com método PATCH para concluir/reabrir a tarefa, `collection` para voltar à lista e links para categorias. O Cliente Web segue esses links, em vez de depender dos endereços dos microserviços.”

#### “Por que não deixar o navegador chamar cada API diretamente?”

> “Isso obrigaria o navegador a conhecer os endereços internos, implementar tratamento de cada serviço e espalharia a lógica de autenticação. Com o Gateway, o cliente conhece uma entrada pública; o Gateway controla acesso e encaminhamento.”

#### “As portas são parte do conceito de microserviço?”

> “Não. As portas 8000, 8001 e 8002 são escolhas para executar os servidores na mesma máquina. A separação vem dos serviços executáveis e de seus contratos. Em outras máquinas, o endereço IP/hostname também distingue os processos.”

#### “Como vocês testaram a integração, e não só cada API isolada?”

> “Além dos testes unitários/contratuais, há um teste ponta a ponta que inicia Gateway, API de tarefas e API de categorias em portas temporárias. Ele cadastra uma conta, faz login, acessa recursos pelo Gateway, cria e consulta tarefa e altera conclusão com PATCH.”

### Perguntas específicas sobre JWT e autenticação

#### “Qual é o fluxo exato do token, desde o login até uma operação?”

> “O Cliente Web envia usuário e senha para `POST /auth/token` (ou cria a conta em `POST /auth/register`). Se os dados estão corretos, o Gateway emite um JWT assinado e devolve o token e links HATEOAS. O JavaScript guarda o token durante a sessão e manda `Authorization: Bearer <token>` nas próximas chamadas. O Gateway valida assinatura e expiração antes de encaminhar o pedido.”

#### “Por que não enviar usuário e senha em cada chamada?”

> “As credenciais são usadas para autenticar uma vez e obter o token. Depois, o cliente envia o JWT, que representa a identidade e expira. Assim a senha não precisa acompanhar as chamadas a tarefas e categorias.”

#### “O que significa Bearer?”

> “Bearer quer dizer que quem apresenta esse token pode usá-lo enquanto ele for válido. Por isso ele deve ser tratado como uma credencial: não deve ser exposto em logs, compartilhado ou colocado em URLs.”

#### “O Gateway confia em qualquer token que tenha formato JWT?”

> “Não. Ele verifica a assinatura com o segredo configurado e confere as claims obrigatórias, incluindo expiração. Um token alterado, expirado ou assinado com outro segredo recebe HTTP 401.”

#### “O token é revogado ao sair da conta?”

> “No protótipo, o logout remove o token da memória do Cliente Web. JWT não tem revogação individual implementada; um token copiado ainda poderia ser usado até expirar. Em produção consideraríamos expiração curta, rotação e/ou lista de revogação, além de HTTPS.”

#### “Por que o token fica em memória no navegador?”

> “O cliente mantém o token apenas durante a página aberta, evitando persistir esse segredo em armazenamento duradouro do navegador. Ao recarregar a página, é preciso entrar novamente. Uma aplicação de produção avaliaria cuidadosamente cookies `HttpOnly` seguros ou outra estratégia de sessão.”

#### “O e-mail é usado para entrar ou recuperar senha?”

> “No projeto, o login usa nome de usuário e senha. O e-mail é coletado e precisa ser único no cadastro, mas ainda não existe confirmação de e-mail nem recuperação de senha.”

### Perguntas específicas sobre Swagger / OpenAPI

#### “O que é Swagger neste projeto?”

> “Swagger UI é uma interface navegável gerada a partir do schema OpenAPI. Ela documenta e permite experimentar as rotas HTTP. A API existe no servidor independentemente do Swagger; a documentação não substitui o Gateway nem a API.”

#### “Onde estão as documentações?”

> “Gateway em `http://<servidor>:8000/docs`, tarefas em `/docs` na porta 8001 e categorias em `/docs` na porta 8002. Cada documentação descreve o contrato público daquele processo.”

#### “Por que existem três páginas Swagger?”

> “Porque são três aplicações HTTP independentes, cada uma com suas próprias rotas e schema. Para apresentar o fluxo do cliente, usamos a documentação do Gateway; as páginas internas ajudam a testar e entender os serviços.”

#### “O botão Authorize faz login?”

> “Não. Primeiro chamamos `/auth/token` ou `/auth/register` para obter o JWT. Depois, no Swagger do Gateway, clicamos `Authorize` e informamos o token como Bearer para experimentar as rotas protegidas.”

#### “O Swagger comprova que a integração está correta?”

> “Ele permite inspecionar e chamar operações, mas sozinho não comprova todo o fluxo. Também executamos testes automatizados e o cenário ponta a ponta que inicia os serviços e chama-os através do Gateway.”

### Perguntas específicas sobre HATEOAS

#### “Como o Cliente Web usa HATEOAS de verdade?”

> “Após receber a resposta de autenticação, guarda os links de tarefas e categorias. Ao listar, usa o link `self`; ao criar, usa o link `create`; para concluir uma tarefa, usa o link `completion` e o método `PATCH`. Ele resolve esses links contra a origem configurada do Gateway, sem apontar para as portas internas.”

#### “Por que cada link tem `href` e `method`?”

> “`href` indica o destino e `method` a operação HTTP esperada. Um link de consulta costuma ser GET; o link `completion` informa PATCH. Isso ajuda o cliente a descobrir ações oferecidas pelo servidor.”

#### “As rotas não continuam escritas no Cliente Web?”

> “O cliente ainda conhece o ponto inicial de autenticação e a origem pública do Gateway. Para navegar entre recursos, segue os links retornados. HATEOAS reduz o acoplamento, mas não elimina a necessidade de um ponto de entrada inicial.”

#### “Se uma resposta não trouxer um link esperado, o que acontece?”

> “O Cliente Web não consegue executar aquela navegação; mostra o erro de link HATEOAS ausente. O link faz parte do contrato e por isso é verificado nos testes de integração.”

### Perguntas específicas sobre o Cliente Web

#### “Qual é a responsabilidade do Cliente Web e o que ele não faz?”

> “Ele apresenta as telas, valida campos básicos no navegador, envia cadastro/login, guarda o JWT durante a sessão, segue links HATEOAS e mostra tarefas, filtros e progresso. Não acessa SQLite nem chama diretamente as APIs internas; essas operações passam pelo Gateway.”

#### “Como o Cliente Web sabe onde está o Gateway?”

> “Por padrão, usa o mesmo host do site com a porta 8000. A URL pode ser definida em `web/config.js`. Assim, ao abrir o site pelo IP do computador servidor, o cliente tenta usar o Gateway nesse mesmo computador.”

#### “Por que às vezes aparece erro de CORS?”

> “O site e o Gateway usam portas diferentes e, para o navegador, isso significa origens diferentes. O Gateway precisa listar a origem exata do site em `CORS_ORIGINS`. Um erro CORS não é corrigido com JWT: primeiro o navegador precisa ter permissão para ler a resposta.”

#### “O Cliente Web poderia acessar direto `:8001` e `:8002`?”

> “Não é o fluxo previsto. Ele deve acessar a porta 8000 do Gateway. Deixar as APIs internas fora do acesso do navegador centraliza validação JWT, roteamento e HATEOAS no ponto de entrada.”

#### “O que é executado no outro notebook durante a apresentação?”

> “Apenas o navegador. O computador servidor executa Cliente Web estático, Gateway e APIs. O navegador baixa HTML/CSS/JavaScript e faz requisições HTTP ao Gateway pelo IP do servidor.”

### Perguntas complementares

### “Por que usar API se os componentes já poderiam se chamar?”

> “A comunicação poderia ser uma chamada interna num monólito. Aqui usamos APIs HTTP porque os componentes são processos separados e o trabalho pede Gateway e dois serviços. O contrato HTTP permite implementá-los e testá-los de forma independente.”

### “O que torna esses componentes microserviços?”

> “Cada serviço tem uma responsabilidade delimitada, uma API própria, processo e porta próprios e pode ser iniciado e testado separadamente. Para este protótipo acadêmico, os três processos rodam na mesma máquina; em produção poderiam estar em hosts distintos.”

### “Por que os serviços estão em portas diferentes?”

> “No desenvolvimento local, as portas distinguem servidores diferentes na mesma máquina. O endereço inclui host e porta. Em computadores diferentes, portas iguais podem ser usadas; o host distingue as máquinas.”

### “Por que uma API usa Django e outra FastAPI?”

> “Frameworks são detalhes de implementação. O que importa na integração é manter métodos, rotas, campos, códigos HTTP e formato de resposta do contrato. O Gateway conversa com ambas via HTTP.”

### “O que ocorre se a API de categorias ficar indisponível?”

> “O Gateway recebe a falha de conexão e responde HTTP 503. A API de tarefas continua sendo um serviço separado; ela valida IDs de categoria localmente contra o contrato e não precisa chamar a API de categorias em toda requisição.”

### “Como os serviços garantem que categorias e tarefas combinam?”

> “Os IDs são strings estáveis como `estudo` e `trabalho`. O serviço de categorias publica a lista; a API de tarefas valida contra os IDs acordados. Há dependência de contrato, mas não de chamada de rede entre esses dois serviços.”

### “Por que guardar `category_id` em vez de uma chave estrangeira?”

> “As categorias pertencem a outro serviço. Em arquitetura de microserviços, normalmente cada serviço administra seus próprios dados; criar uma chave estrangeira entre bancos de serviços acoplaria os bancos. Aqui o ID estável é uma referência compartilhada pelo contrato.”

### “O que o JWT contém? Como é verificado?”

> “O token contém a identidade no campo `sub` e expiração. É assinado com um segredo do Gateway; nas rotas protegidas, assinatura e expiração são verificadas. A senha não é enviada para cada chamada.”

### “JWT é criptografado?”

> “Neste projeto, não. O JWT é assinado, não cifrado: a assinatura permite detectar alteração, mas o payload não deve conter segredo. Por isso usamos nele apenas identidade e expiração.”

### “As senhas ficam salvas no banco?”

> “Não em texto puro. Guardamos um hash scrypt com sal e verificamos a senha comparando o resultado. Segredos de demonstração e bancos locais não devem ser publicados.”

### “Qualquer pessoa pode criar uma conta?”

> “No protótipo, sim: o cadastro está aberto e não há verificação de e-mail nem recuperação de senha. Essas seriam melhorias necessárias num sistema real.”

### “Como impedem alguém de acessar tarefas de outra conta?”

> “O Gateway verifica o JWT e encaminha o usuário autenticado pelo cabeçalho interno `X-User-Id`. A API filtra e altera tarefas por esse proprietário; o Cliente Web não pode escolher esse cabeçalho pelo fluxo público.”

### “O que significa HATEOAS neste sistema?”

> “As respostas incluem links com `href` e `method`, por exemplo um link de `completion` PATCH. O cliente navega seguindo os links devolvidos pelo Gateway em vez de conhecer rotas internas.”

### “CORS protege a API?”

> “Não é autenticação. CORS é uma política do navegador sobre quais origens web podem ler as respostas. O JWT protege rotas e o firewall controla conectividade da rede.”

### “O que acontece se o Gateway parar?”

> “O Cliente Web perde seu ponto de entrada e não consegue acessar tarefas/categorias. Isso torna o Gateway um componente crítico; numa solução de produção poderia haver várias instâncias e balanceamento.”

### “Por que SQLite? É adequado para muitos usuários?”

> “SQLite é simples e suficiente para demonstração local. Para múltiplos servidores, alta concorrência ou produção, escolheríamos um banco servidor, como PostgreSQL, e configuraríamos backup e migrações.”

### “Os dados são compartilhados se cada amigo iniciar o projeto no próprio computador?”

> “Não. Cada execução tem seus bancos SQLite locais. Para todos usarem os mesmos dados, os serviços e bancos precisam rodar numa instância servidora comum acessível pela rede.”

### “Por que o notebook cliente não precisa de Python?”

> “O servidor entrega arquivos HTML/CSS/JavaScript. O navegador os executa e faz requisições HTTP para o Gateway; o cliente não executa os servidores Python.”

### “O que fazem os códigos HTTP?”

> “Usamos, entre outros: 200 para consulta/atualização bem-sucedida, 201 para criação, 400 para dados inválidos, 401 para falta/invalidade de JWT, 404 para recurso não encontrado e 503 quando um serviço interno está indisponível.”

### “Isso está pronto para produção?”

> “Não. É uma demonstração acadêmica: usa conta demo configurável, sem verificação de e-mail, sem recuperação de senha, usa SQLite e precisa de TLS, gestão robusta de segredos, proteção contra abuso e operação monitorada para produção.”

## 7. Checklist antes de apresentar

### Aplicação e rede

- [ ] Todos os quatro processos iniciam sem erro.
- [ ] O Gateway e cada API respondem em `/health`.
- [ ] O computador cliente abre `http://<IP-DO-SERVIDOR>:5500`.
- [ ] O cliente consegue entrar, carregar categorias e tarefas, criar uma tarefa e concluir/reabrir.
- [ ] `CORS_ORIGINS` contém a origem exata usada pelo navegador.
- [ ] O firewall permite as portas 5500 e 8000 na rede privada.
- [ ] As URLs e o IP são os da rede em que ocorrerá a apresentação; não usar IP antigo.

### Demonstração técnica

- [ ] Login/cadastro funciona e credenciais de demonstração estão preparadas.
- [ ] Rota protegida sem JWT responde 401.
- [ ] Token válido permite acesso.
- [ ] Respostas mostram links HATEOAS relevantes.
- [ ] Swagger abre para Gateway e para os dois serviços.
- [ ] Ninguém publica `.env`, segredo JWT, banco de contas ou dados pessoais.

### Preparação da fala

- [ ] Cada integrante sabe explicar uma responsabilidade e o fluxo completo.
- [ ] Cada integrante consegue dizer o que acontece se seu serviço parar.
- [ ] Uma pessoa do grupo pode demonstrar o sistema sem depender do computador do desenvolvedor.
- [ ] Há um plano caso o Wi-Fi do laboratório bloqueie conexões entre notebooks (por exemplo, usar a mesma máquina para cliente e serviços, ou outra rede autorizada).

## 8. Limites conhecidos e melhorias possíveis

- Cadastro aberto, sem confirmação de e-mail, redefinição de senha ou política contra abuso.
- Categorias estáticas; para uma lista administrável seria necessário persistir categorias no serviço correspondente.
- O gateway transmite o usuário à API de tarefas por uma rede interna de confiança. Se o serviço fosse exposto diretamente, seria preciso reforçar autenticação entre serviços.
- SQLite local e conta demo destinam-se a uma demonstração, não a implantação escalável.
- IP privado pode mudar ao reconectar à rede; confirmar novamente no dia.
