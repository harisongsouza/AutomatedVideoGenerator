#LEMBRE-SE: SELECIONE 1 IMAGEM A FRENTE DA IMAGEM QUE VOCE QUER PARA PEGAR A IMAGEM QUE VOCE QUER.
Add-Type -AssemblyName System.Web
Add-Type -AssemblyName System.Windows.Forms

function Remover-UUID {
    param (
        [string]$texto
    )
    $regex = '\b[0-9a-fA-F]{8}(-?[0-9a-fA-F]{4}){3}-?[0-9a-fA-F]{12}\b'
    $resultado = $texto -replace $regex, ''
    $resultado = $resultado -replace '\s{2,}', ' '
    return $resultado.Trim()
}

$entrada = $args[0]

$stringMinuscula = $entrada.ToLower()
$stringModificada = Remover-UUID $stringMinuscula
$busca = "`"$stringModificada`""
$termoURL = [System.Web.HttpUtility]::UrlEncode($busca)
$url = "https://duckduckgo.com/?q=$termoURL&iax=images&ia=images"

# Caminho para navegador
$chromePath = "C:\Program Files\Mozilla Firefox\firefox.exe"
Start-Process $chromePath "--new-window $url"

# Ativa janela
$wshell = New-Object -ComObject wscript.shell
$wshell.AppActivate("Mozilla Firefox")
Start-Sleep -Seconds 2

# Cola o código JavaScript no console do navegador
Set-Clipboard '
(() => {
  const delay = ms => new Promise(r => setTimeout(r, ms));
  const urls = [];
  let ultimaUrl = "";
  let imagemCount = 0;

  async function esperarImagemGrandeESalvarUrl() {
    await delay(100); // Reduzido de 200ms para iniciar a verificação mais cedo
    let tentativas = 0;
    let novaUrl = "";

    while (tentativas < 20) { // Mantém 20 tentativas, mas com intervalos menores
      await delay(150); // Reduzido de 200ms para verificar mais frequentemente
      const imgAlta = document.querySelector("img.d1fekHMv2WPYZzgPAV7b");
      if (imgAlta && imgAlta.src) {
        novaUrl = imgAlta.src.startsWith("//") ? "https:" + imgAlta.src : imgAlta.src;
        // Esta condição tenta sair do loop assim que uma URL diferente da última capturada for encontrada.
        // Isso pressupõe que a primeira URL nova encontrada é a da imagem clicada.
        if (novaUrl && novaUrl !== ultimaUrl) { // Adicionada verificação de novaUrl não ser vazia aqui também
            break;
        }
      }
      tentativas++;
      // Se a imagem não mudar, mas novaUrl for igual a ultimaUrl, o loop continua
      // até o limite de tentativas, evitando loops infinitos se a imagem não carregar ou for a mesma.
      if (novaUrl && novaUrl === ultimaUrl && imgAlta && imgAlta.src) {
          // Se a imagem no visualizador é a mesma que já foi processada,
          // e não esperamos mais mudanças (ou a imagem clicada é a mesma da anterior),
          // podemos sair para evitar espera desnecessária se o usuário clicar na mesma imagem.
          // No entanto, para o problema de pegar a "próxima", o foco é no break acima.
          // Esta parte é mais para otimizar se a imagem correta já foi pega e não muda.
          // Se a imagem clicada é realmente a mesma que ultimaUrl,
          // o segundo if (fora do while) impedirá o re-salvamento.
      }
    }

    if (novaUrl && novaUrl !== ultimaUrl) {
      ultimaUrl = novaUrl;
      urls.push(novaUrl);
      imagemCount++;
      console.log(`🔗 Link da imagem ${imagemCount} capturado: ${novaUrl}`);

      // Salvar url.txt
      const blob = new Blob([urls.join("\n")], { type: "text/plain" });
      const urlObjeto = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = urlObjeto;
      a.download = "urls.txt";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(urlObjeto);
      console.log("📁 Arquivo urls.txt salvo.");
    } else if (!novaUrl) {
      console.log("❌ Imagem grande não encontrada ou URL não pôde ser lida após tentativas.");
    } else {
      console.log("ℹ️ Imagem não carregada, já salva anteriormente, ou nenhuma nova imagem detectada.");
    }
  }

  const miniaturas = document.querySelectorAll("ol > li ol > li img");
  if (miniaturas.length === 0) {
    console.log("❌ Nenhuma miniatura encontrada.");
  } else {
    console.log("🟢 Clique em uma miniatura para capturar a URL da imagem grande.");
    miniaturas.forEach(miniatura => {
      miniatura.style.border = "2px solid red";
      miniatura.addEventListener("click", () => {
        // Reduzido o delay antes de chamar a função para tentar ser mais rápido
        setTimeout(esperarImagemGrandeESalvarUrl, 250); // Reduzido de 500ms
      });
    });
  }
})();
'

# Abrir console, colar e executar o JS
$shell = New-Object -ComObject WScript.Shell
$shell.SendKeys('{F12}')
Start-Sleep -Seconds 2
$shell.SendKeys('^{SHIFT}K')
Start-Sleep -Seconds 2
$shell.SendKeys('^v')
Start-Sleep -Seconds 1
$shell.SendKeys('{ENTER}')
Start-Sleep -Milliseconds 500
$shell.SendKeys('{F12}')
Start-Sleep -Seconds 2

# Espera o download do arquivo urls.txt na pasta Downloads
$downloadsPath = [Environment]::GetFolderPath("UserProfile") + "\Downloads"
$arquivoDestino = Join-Path $downloadsPath "urls.txt"
$timeout = 180
$tempoEsperado = 0

while (-not (Test-Path $arquivoDestino) -and ($tempoEsperado -lt $timeout)) {
    Start-Sleep -Seconds 1
    $tempoEsperado++
}

# Finaliza o navegador
$shell.SendKeys('^w')

Write-Output "#LEMBRE-SE: SELECIONE 1 IMAGEM A FRENTE DA IMAGEM QUE VOCE QUER PARA PEGAR A IMAGEM QUE VOCE QUER."
