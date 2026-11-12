# 03 · Baixar o dArkOSRE

## Objetivo

Baixar a imagem oficial e confirmar que ela está íntegra.

## Pré-requisitos

- ~12 GB livres (o `.7z` mais o `.img` extraído).

## Passos

1. Fonte oficial: o GitHub **southoz/dArkOSRE-R36**, página de releases. A release 03082026 aponta para Mega, Google Drive, OneDrive e um torrent dentro do próprio repositório (`resources/torrent/`).
2. O que funcionou para nós:
   - **Google Drive:** "Quota exceeded".
   - **Torrent:** nenhum peer em 6 minutos.
   - **Mega:** ~16 MB/s com o `megatools` (`brew install megatools`):

```bash
megatools dl --path . "https://mega.nz/file/<id>#<chave>"
```

3. Extraia:

```bash
7z t dArkOSRE_R36_trixie_03082026.7z && 7z x dArkOSRE_R36_trixie_03082026.7z
```

4. **Confira o SHA1 do `.img` extraído.** O hash publicado na release é o da imagem, não o do `.7z`:

```bash
sha1sum dArkOSRE_R36_trixie_03082026.img   # deve bater com o da release
```

## Verificação

- O SHA1 do `.img` é igual ao da release (03082026: `a4858eee2f1eced10d3ce90c911d89450eea700f`).
- Conferência extra: o `.7z` bate peça por peça com o `.torrent` do repositório:

```bash
aria2c -V --seed-time=0 --bt-stop-timeout=1 --enable-dht=false -d . -T arquivo.torrent
```

## Problemas conhecidos

| Sintoma | Causa | Solução |
|---|---|---|
| SHA1 "não bate" | Você conferiu o `.7z` | Confira o `.img` |
| `.img` menor que o esperado (ex.: 3 GB em vez de 8,3 GB) | Extração interrompida | Apague e extraia de novo |
