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