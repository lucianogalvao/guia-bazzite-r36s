# Curadoria de ROMs

Duas etapas, sem dependências além do Python 3:

```bash
python3 inventario.py /caminho/roms > inv.json    # lista bruta
python3 agrupar.py inv.json roms.json             # agrupa por jogo e sugere uma versão
```

O `roms.json` serve de base para escolher: numa planilha, num script ou numa página simples. A primeira versão de cada jogo é a sugerida.

| Regra | Efeito |
|---|---|
| Extensões `.mp4 .old .nv .hi .fs .glshadercache .sfo .ppst .rtc` | Ignoradas (vídeos, configs do MAME, cache) |
| Pastas `ppsspp`, `downloaded_videos`, `media` | Ignoradas |
| Título sem numeração, região e tags | Junta "0001 Rockman 1.gb" com "Rockman 1 (Japan).gb" |
| Proto/beta/demo/hack/unl, `[b]` `[h]` | Marcados como lixo e vão para o fim |
| Preferência | Tem save > PT-BR > USA > World > Europa > Japão, e a Rev mais alta |

Nos arcades (MAME, Neo Geo, CPS), os nomes são curtos (`sf2.zip`) e não agrupam por título.

**Não** versione o `inv.json` nem o `roms.json`: eles listam a sua coleção.
