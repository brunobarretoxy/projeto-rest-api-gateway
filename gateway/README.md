# Responsabilidade de Bruno — Gateway

O Gateway é o único ponto de entrada do cliente: emite JWT de demonstração, valida o bearer token, encaminha chamadas para as APIs internas, traduz indisponibilidade dos serviços e adiciona links HATEOAS.

A documentação interativa fica em `http://127.0.0.1:8000/docs` quando o servidor estiver em execução. A visão de rotas e os contratos compartilhados estão em [../docs/contrato-api.md](../docs/contrato-api.md).

Configurações por ambiente: `JWT_SECRET`, `JWT_ALGORITHM`, `JWT_EXPIRE_MINUTES`, `DEMO_USERNAME`, `DEMO_PASSWORD`, `TASKS_API_URL` e `CATEGORIES_API_URL`. Não compartilhe um `.env` real no GitHub; o `.env.example` contém apenas valores locais de demonstração.
