# PYStem

Separação de áudio local e gratuita, em CPU. O Demucs continua a ser o motor
predefinido; MDX23C e BS-Roformer usam adaptadores opcionais para um checkout
local do Music Source Separation Training (MSST).

## Instalar e usar

Python 3.11 e FFmpeg no PATH (incluindo `ffprobe`). No PowerShell, na raiz do projeto:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe src\main.py
# Ou sem menu:
.\.venv\Scripts\python.exe src\main.py "C:\audio\musica.flac" --model htdemucs --threads 4
```

Modelos registados: `htdemucs`, `htdemucs_ft`, `htdemucs_6s`, `mdx23c` e
`bs_roformer`. Resultados: `output/<modelo>/<nome do áudio>/`. A função existente
`separate_audio(audio_path, output_dir="output")` mantém o retorno booleano e o
HTDemucs predefinido. O menu permite selecionar modelos e os caminhos opcionais.

Todos os adaptadores usam CPU, quatro threads por omissão e timeout de 30 minutos
(ajustável com `--threads` e `--timeout`, em segundos). A entrada é isolada numa
pasta temporária para impedir que o MSST processe músicas vizinhas. Ficheiros de
saída antigos não podem mascarar uma inferência sem resultados.

**Mudança intencional:** a separação não descarrega pesos automaticamente.
`HF_HUB_OFFLINE=1` e um bloqueio das ligações de rede Python impedem downloads
implícitos dos motores. O Demucs precisa dos pesos já presentes na cache do seu
ambiente. Uma cache em falta dá erro; o provisionamento deve ser feito à parte.
O bloqueio não é uma barreira de segurança contra código local malicioso ou
bibliotecas nativas: executar apenas motores, YAML e checkpoints de confiança.

## MDX23C e BS-Roformer opcionais

Usar um ambiente separado: o ambiente Demucs existente usa NumPy 1.26, enquanto
o MSST atual declara NumPy >=2. Não instalar as dependências opcionais na `.venv`.
O adaptador foi preparado para a interface `inference.py` do MSST no commit
`6fdad13686bb7e84d029ec66f9dbe76e65c93ebf`; não depende de uma API `msst` presumida.

```powershell
git clone https://github.com/ZFTurbo/Music-Source-Separation-Training.git .tools/msst
git -C .tools/msst checkout 6fdad13686bb7e84d029ec66f9dbe76e65c93ebf
python -m venv .venv-models
.\.venv-models\Scripts\python.exe -m pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv-models\Scripts\python.exe -m pip install -r requirements-models.txt
```

O ficheiro opcional contém apenas as dependências de inferência necessárias para
estas duas arquiteturas. Não instala a lista completa de treino/GUI do MSST.
Rever espaço para pesos, ambiente, cache do instalador, áudio temporário e saídas.

```powershell
# Apenas mostra os tamanhos e verifica espaço; não descarrega:
.\.venv\Scripts\python.exe src\download_models.py
# Depois de aprovar os tamanhos e termos dos pesos:
.\.venv\Scripts\python.exe src\download_models.py --allow-download

.\.venv\Scripts\python.exe src\main.py "C:\audio\musica.wav" --model mdx23c --msst-dir .tools/msst --python .venv-models/Scripts/python.exe --checkpoint models/mdx23c/model.ckpt --config models/mdx23c/config.yaml
# Para BS-Roformer, trocar o modelo por bs_roformer e os caminhos pela pasta models/bs_roformer.
```

Os adaptadores MSST destinam-se aos checkpoints vocais documentados abaixo e
exigem `vocals.wav` e `instrumental.wav`; o MDX23C pode também produzir `other.wav`.
O instrumental é calculado por subtração da estimativa vocal. Outros checkpoints
multistem requerem adaptar o catálogo e a validação dos stems.
Um YAML temporário mantém as dimensões do modelo e altera apenas
`inference.batch_size=1` e `training.use_amp=False`. Os originais ficam intactos.
Sem CUDA, a atenção do Roformer deve usar a implementação CPU disponível no PyTorch.

## Pesos gratuitos e licenças — investigação de 29/10/2026

| Candidato | Checkpoint público | Tamanho verificado |
| --- | --- | ---: |
| MDX23C, ZFTurbo/MVSep | `model_vocals_mdx23c_sdr_10.17.ckpt` | 448 101 203 bytes (~427 MiB) |
| BS-Roformer, viperx | `model_bs_roformer_ep_317_sdr_12.9755.ckpt` | 639 331 213 bytes (~610 MiB) |

Os pares YAML/checkpoint estão ligados na [lista oficial do MSST](https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/6fdad13686bb7e84d029ec66f9dbe76e65c93ebf/docs/pretrained_models.md).
O MDX23C está na [release v1.0.0](https://github.com/ZFTurbo/Music-Source-Separation-Training/releases/tag/v1.0.0)
e o viperx na [release pública UVR](https://github.com/TRvlvr/model_repo/releases/tag/all_public_uvr_models).
Os tamanhos foram consultados através dos metadados das releases, sem descarregar
os pesos nessa consulta. Posteriormente, ambos foram descarregados com autorização
do utilizador, depois de verificar cerca de 660 GiB livres no disco.

O [código MSST é MIT](https://github.com/ZFTurbo/Music-Source-Separation-Training/blob/6fdad13686bb7e84d029ec66f9dbe76e65c93ebf/LICENSE).
Isso não confirma, por si só, uma licença dos dois checkpoints escolhidos.
Existe uma [discussão com respostas do autor sobre licenças de pesos](https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/245),
incluindo autorizações para outros modelos; não se deve extrapolá-las para todos
os autores/checkpoints. Nesta investigação não foi confirmada uma declaração
inequívoca que cubra especificamente ambos os ficheiros acima. Não redistribuir
os pesos com o PYStem nem anunciar permissão comercial com base apenas na licença
do código. Gratuito para descarregar não significa licença permissiva confirmada.
O Demucs mantém a integração existente; verificar separadamente os termos dos seus
pesos antes de qualquer distribuição pública.

`download_models.py` exige `--allow-download`, verifica espaço com reserva de 2 GB,
confere o tamanho de cada checkpoint, limita os YAML a 1 MiB, recusa sobrescrever
ficheiros e grava URL, autor, tamanho e SHA-256 em `models/<modelo>/manifest.json`.
Hashes são calculados localmente, não assinaturas autenticadas pelos autores.
`models/`, `.tools/`, ambientes e saídas estão excluídos do Git.

## Testes e benchmarks CPU

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m pip install -r requirements-benchmark.txt
# Gera 8 segundos de tons estéreo determinísticos e executa duas vezes:
.\.venv\Scripts\python.exe src\benchmark.py --report-dir output/benchmarks/meu-teste
# Com um excerto musical autorizado e ambiente opcional:
.\.venv\Scripts\python.exe src\benchmark.py "C:\audio\excerto.wav" --model bs_roformer --report-dir output/benchmarks/roformer --msst-dir .tools/msst --python .venv-models/Scripts/python.exe --checkpoint models/bs_roformer/model.ckpt --config models/bs_roformer/config.yaml --timeout 300
```

Cada pasta de relatório tem de ser nova. O benchmark grava JSON e logs, duração,
fator de tempo real (tempo de execução / duração do áudio; menor é melhor), RSS
amostrado do processo e descendentes, versões, hashes dos ficheiros fornecidos e
validação de duração, taxa de amostragem, canais e valores finitos dos stems.
Usar `--artifact <ficheiro>` repetidamente para identificar também os pesos Demucs
da cache. O ambiente do motor opcional e o commit MSST são registados no JSON.
Para comparar estes checkpoints, usar entrada estéreo a 44 100 Hz; outros formatos
podem ser reamostrados pelo motor e serão assinalados como formato diferente pelo
validador estrito, mesmo quando a separação em si terminou corretamente.

O tempo inclui importação, carregamento, cópia temporária e exportação: não é só
inferência. Cada repetição cria um processo novo; a cache de ficheiros do sistema
pode estar quente. A memória é a soma RSS amostrada a cada 100 ms, podendo contar
páginas partilhadas mais de uma vez e perder picos breves. Para comparar, usar o
mesmo excerto, threads, configurações e estado energético do portátil; não executar
os modelos em simultâneo. O Demucs mantém os parâmetros padrão de separação.

## Resultados locais

Hardware confirmado: AMD Ryzen 7 5825U, 16 processadores lógicos, aproximadamente
31,4 GiB de RAM, Windows, Python 3.11.9. Sem CUDA.

HTDemucs (Demucs 4.1.0, PyTorch 2.14.1, NumPy 1.26.4), quatro threads, entrada
sintética de 8 s, estéreo, 44 100 Hz:

| Ensaio | Tempo total | Fator de tempo real | RSS amostrado da árvore |
| --- | ---: | ---: | ---: |
| 1 | 11,17 s | 1,40 | 0,99 GiB |
| 2 | 10,68 s | 1,33 | 1,03 GiB |

Ambos terminaram com quatro stems válidos, finitos e com duração, canais e taxa
de amostragem iguais à entrada. Pesos HTDemucs da cache, sem novo download.
Relatório local: `output/benchmarks/cpu-2026-10-29-htdemucs/report.json`.

MDX23C (MSST no commit indicado, PyTorch/Torchaudio 2.6.0+cpu, NumPy 2.2.6), mesmo
áudio e quatro threads, lote 1, AMP desligado, overlap original 4:

| Ensaio | Tempo total | Fator de tempo real | RSS amostrado da árvore |
| --- | ---: | ---: | ---: |
| 1 | 130,54 s | 16,32 | 2,57 GiB |
| 2 | 107,27 s | 13,41 | 2,46 GiB |

Ambos produziram `vocals.wav`, `other.wav` e `instrumental.wav` válidos e com
formato igual à entrada. O primeiro ensaio inclui custos iniciais do ambiente
opcional, incluindo possível compilação/cache de rotinas de áudio.
BS-Roformer viperx (mesmo ambiente opcional e entrada), quatro threads, lote 1,
AMP desligado, overlap original 2:

| Ensaio | Tempo total | Fator de tempo real | RSS amostrado da árvore |
| --- | ---: | ---: | ---: |
| 1 | 148,99 s | 18,62 | 2,74 GiB |
| 2 | 155,08 s | 19,38 | 2,74 GiB |

Ambos produziram `vocals.wav` e `instrumental.wav` válidos, finitos e com o formato
da entrada. Os seis ensaios usaram a mesma entrada (SHA-256
`fb1cce7eb57094256b8b7e77800429e7536295921b3670dd802c0eaf831c4f66`).
Os modelos têm janelas, overlap e stems diferentes; estes valores descrevem o
custo das configurações testadas, não uma comparação isolada das arquiteturas.
Neste teste, o HTDemucs foi o mais rápido. Não é possível concluir qual tem melhor
qualidade de separação a partir destes tempos ou deste áudio sintético.

Relatórios JSON preservados em `docs/benchmarks/`; os manifests dos pesos em
`docs/model-artifacts.json`; versões exatas do ambiente opcional em
`docs/models-environment-lock.txt`. Para reproduzir esse ambiente, instalar a
lista com `--extra-index-url https://download.pytorch.org/whl/cpu`, numa venv
separada. Os 16 testes automáticos passaram, incluindo o protocolo MSST com motor
simulado; esses testes não substituem os ensaios de inferência reais acima.

Não foram calculados SDR/SI-SDR: não há stems de referência de um conjunto musical
de avaliação. Tons sintéticos verificam funcionamento, não qualidade em metal,
rock ou EDM. Também não permitem extrapolar o tempo para músicas completas.
O relato histórico em `docs/diario.md` não é um benchmark controlado desta sessão.
