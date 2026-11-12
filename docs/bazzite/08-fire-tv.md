# 08 · Moonlight no Fire TV Stick

## Objetivo

Jogar na TV da sala com baixo atraso, usando o Modo Jogo da TV pela entrada HDMI.

## Pré-requisitos

- Sunshine funcionando ([07](07-sunshine.md)).
- Fire TV Stick 4K Max (2ª geração) com a **fonte original na tomada**. A USB da TV costuma não dar conta.

## Passos

1. Faça a configuração inicial e deixe o Stick **atualizar**.
2. Conecte no **Wi-Fi de 5 GHz**.
3. Instale o **Moonlight Game Streaming** pela Amazon Appstore.
4. No Moonlight: **"+" → IP-DO-PC** (a descoberta automática não acha o PC). O app mostra um PIN. Digite-o no painel do Sunshine, na aba **PIN**.
5. **Configurações do Moonlight:**

| Opção | Valor |
|---|---|
| Resolução / FPS | 1080p / 60 |
| Bitrate | 30 Mbps |
| Codec | HEVC |
| HDR | Ligado, se o Game Mode estiver em HDR (veja [10](10-problemas.md)) |
| Forçar faixa completa de cor | **Desligado** |
| Mostrar estatísticas de desempenho | Ligado, para testar |

6. **Controles Xbox:** Configurações → Controles e Dispositivos Bluetooth → Controles de Jogos → Adicionar. Segure o botão de parear até o logo piscar rápido. O controle guarda um aparelho por vez: ao parear no Stick, ele esquece o PC.
7. **TV Samsung:** Configurações → Geral → Gerenciador de dispositivos externos → **Modo Jogo** e **Jogo HDR** ligados, **Anynet+ (HDMI-CEC)** ligado.
8. **Atalhos no stream:** `Select + Start + LB + RB` encerra. Segurar o botão Menu (☰) por 1 s transforma o analógico em mouse.

## Verificação

Jogue 10–15 minutos com as estatísticas ligadas. Resultado no nosso teste, pelo Wi-Fi 5 GHz com o roteador ao lado da TV:

| Métrica | Medido | Ideal |
|---|---|---|
| FPS | 59–60 | 60 |
| Quadros perdidos pela rede | 0% | perto de 0% |
| Latência de rede | 2–7 ms | < ~10 ms |
| Decodificação | ~4 ms | poucos ms |

Com números assim, o adaptador Ethernet (10/100) não é necessário.

## Problemas conhecidos

| Sintoma | Solução |
|---|---|
| "Procurando PCs" para sempre | Adicione pelo IP com "+" |
| Erro 503 ou "código -1" ao conectar | Veja [10](10-problemas.md) |
| Imagem escura | Veja [10](10-problemas.md) |
| Configuração do bitrate não salva | Ajuste o controle deslizante e saia com Voltar antes de conectar |
| Tela inicial poluída | O Fire OS não deixa trocar o launcher. Desligue a reprodução automática (Preferências → Conteúdo em destaque) e os dados de uso (Preferências → Privacidade) |
