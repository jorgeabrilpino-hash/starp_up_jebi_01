# Inputs

Los inputs esperados por el proyecto son:

- `shovel_left.mp4`
- `shovel_right.mp4`
- `imu_data.npy`

## Nota importante

Los dos videos pesan más de 100 MB, así que GitHub no permite versionarlos directamente en este repo sin Git LFS.

Por eso este proyecto incluye una forma reproducible de preparar `inputs/`:

## Opción 1: enlazar archivos locales ya descargados

```bash
bash scripts/setup_inputs_local.sh
```

Esto crea enlaces simbólicos desde rutas locales conocidas hacia `inputs/`.

## Opción 2: descargar videos desde Google Drive

```bash
python scripts/download_inputs.py
```

Luego podrás ejecutar:

```bash
bash run.sh
```
