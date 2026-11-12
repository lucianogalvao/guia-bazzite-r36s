# 02 · Discos

## Objetivo

Separar sistema, jogos e ROMs em discos diferentes, montados sozinhos a cada boot.

| Disco | Conteúdo | Por quê |
|---|---|---|
| SSD (sistema) | Bazzite, configurações, emuladores | O sistema ocupa uns 30–40 GB |
| NVMe 1 TB | Biblioteca Steam, Switch, PS3, Battle.net | Jogos modernos leem do disco o tempo todo |
| HD 1 TB | ROMs retrô (CHD/RVZ), downloads, backups | Jogos retrô quase não leem do disco |

## Pré-requisitos

- Backup do que houver nos discos: eles serão formatados.
- **Não use NTFS** para jogos. O Proton tem problemas com ele.

## Passos

1. Confira qual disco é qual **antes de apagar**:

```bash
lsblk -o NAME,SIZE,MODEL,FSTYPE,LABEL
```

2. Formate em ext4 com rótulos fáceis (exemplo, troque os dispositivos pelos seus):

```bash
sudo mkfs.ext4 -L jogos /dev/nvme0n1p1
sudo mkfs.ext4 -L roms  /dev/sdY1
```

3. Libere o espaço reservado do ext4 (~46 GB a mais por disco de 1 TB):

```bash
sudo tune2fs -m 0 /dev/nvme0n1p1
sudo tune2fs -m 0 /dev/sdY1
```

4. Monte pelo UUID em `/var/mnt`, com `nofail`, para o PC ligar mesmo se um disco falhar:

```bash
sudo blkid -s UUID -o value /dev/nvme0n1p1     # anote os UUIDs
sudo cp /etc/fstab /etc/fstab.bak-$(date +%F)
echo 'UUID=<uuid-jogos> /var/mnt/jogos ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
echo 'UUID=<uuid-roms>  /var/mnt/roms  ext4 defaults,nofail 0 2' | sudo tee -a /etc/fstab
sudo mkdir -p /var/mnt/jogos /var/mnt/roms && sudo systemctl daemon-reload && sudo mount -a
sudo chown "$USER:" /var/mnt/jogos /var/mnt/roms
```

5. **Biblioteca Steam no NVMe, pelo Modo Desktop.** O Game Mode não mostra discos em `/var/mnt`. Abra a Steam no Desktop → Configurações → Armazenamento → Adicionar unidade → `/var/mnt/jogos`, e marque como padrão. Remova bibliotecas antigas indisponíveis.

## Verificação

```bash
findmnt /var/mnt/jogos /var/mnt/roms
```

Reinicie e confira que os dois montaram sozinhos.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| Biblioteca antiga "indisponível" na Steam | Remova em Configurações → Armazenamento |
| O disco não aparece no Game Mode | Adicione pela Steam no Modo Desktop |
