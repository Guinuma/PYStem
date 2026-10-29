# PYStem — Diário de Desenvolvimento

## Sessão 01 — 08/10/2026

### Objetivo
Iniciar o desenvolvimento do PYStem, uma aplicação Python para separar músicas em diferentes pistas de áudio utilizando inteligência artificial.

### O que fizemos
- Criámos o repositório GitHub `Guinuma/PYStem`.
- Configurámos o Git e sincronizámos o projeto.
- Instalámos o Python 3.11.9 e criámos o ambiente virtual `.venv`.
- Instalámos o Demucs, PyTorch e NumPy.
- Criámos a estrutura inicial do projeto.
- Implementámos a separação de áudio através do Demucs.
- Adicionámos validação de ficheiros e tratamento de erros.
- Criámos um menu interativo no terminal.

### Problemas encontrados
**PowerShell bloqueava a ativação do ambiente virtual.**

Solução: alterar temporariamente a política de execução para a sessão atual.

**O Demucs não encontrava o NumPy.**

Solução: instalar uma versão compatível do NumPy no ambiente virtual.

### Primeiro teste real
**Música:** VIANOVA — Squier Talk

**Formato de entrada:** FLAC

**Modelo:** HTDemucs

**Tempo de processamento:** aproximadamente 2 minutos e 3 segundos.

**Resultado:** quatro ficheiros WAV:
- `vocals.wav`
- `drums.wav`
- `bass.wav`
- `other.wav`

A separação apresentou alguns artefactos, mas permitiu ouvir os vocais isolados da música.

### Conceitos aprendidos
- Ambientes virtuais Python
- Instalação e gestão de dependências com pip
- Funções e parâmetros opcionais
- Estruturas condicionais e ciclos
- Validação de caminhos com `pathlib`
- Execução de processos externos com `subprocess`
- Tratamento de erros com `try` e `except`
- Organização de projetos Python

### Próximos objetivos
- [ ] Implementar reprodução de áudio.
- [ ] Adicionar controlos Play/Pause.
- [ ] Permitir ouvir stems individualmente.
- [ ] Desenvolver uma interface gráfica.
- [ ] Melhorar a documentação do projeto.

---

**Estado:** Primeira versão funcional em linha de comandos.

## Sessão 02 — 29/10/2026

### Seleção modular e CPU

- Mantida a função pública `separate_audio` e o HTDemucs predefinido, com os
  mesmos quatro stems e estrutura de saída.
- Introduzidos catálogo de modelos, adaptador Demucs e adaptador MSST para
  MDX23C e BS-Roformer vocais, selecionáveis pelo menu e por argumentos CLI.
- A inferência usa apenas ficheiros locais; downloads passaram para um comando
  separado e explícito, com verificação de espaço, tamanhos e manifests SHA-256.
- Depois de autorização expressa do utilizador, descarregados os dois checkpoints
  e respetivos YAML, sem os adicionar ao Git.
- Criada `.venv-models` com PyTorch/Torchaudio 2.6.0+cpu e NumPy 2.2.6. O ambiente
  Demucs original manteve as suas versões e passou a verificação de dependências.
- MSST fixado no commit `6fdad13686bb7e84d029ec66f9dbe76e65c93ebf`, sem alterações
  ao código upstream. O perfil temporário CPU usa lote 1 e AMP desligado.
- Passaram 16 testes automáticos. Executados ensaios de inferência reais com os
  três motores no Ryzen 7 5825U, sem CUDA; resultados e limites no README e nos
  relatórios JSON em `docs/benchmarks/`.

### Limitações

Os ensaios usam oito segundos de tons estéreo, úteis para verificar funcionamento,
formato, velocidade e memória. Não medem qualidade de separação em música e não
permitem escolher um modelo por género. Faltam excertos autorizados com stems de
referência e avaliação auditiva. As licenças específicas dos dois checkpoints
novos continuam sem confirmação inequívoca para redistribuição; não confundir a
licença MIT do motor MSST com a licença de todos os pesos disponíveis.

### Git

Por indicação do utilizador, realizar commits por blocos validados e enviá-los
regularmente para o GitHub. Pesos, ambientes e áudio ficam excluídos do Git.
