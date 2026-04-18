# JEBI OEP MVP v2

MVP escalable para calcular un **Operator Efficiency Profile (OEP)** con video estéreo + IMU.

## Estructura

```text
solution/
  main.py
  oep/
    config.py
    imu.py
    video.py
    scoring.py
    reporting.py
    advisor.py
    pipeline.py
```

## Ejecución

```bash
bash run.sh
```

## Inputs esperados

```text
inputs/shovel_left.mp4
inputs/shovel_right.mp4
inputs/imu_data.npy
```

## Outputs

```text
outputs/oep_report.json
outputs/oep_summary.txt
outputs/oep_visualization.png
outputs/dashboard/index.html
```

## IA opcional

### OpenAI
```bash
export USE_AI_ADVISOR=1
export OPENAI_API_KEY=tu_api_key
export OPENAI_MODEL=gpt-4o-mini
bash run.sh
```

### Ollama
```bash
export USE_AI_ADVISOR=1
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=llama3.1:8b
bash run.sh
```

Si no hay IA disponible, el pipeline sigue funcionando igual.
