
$entrada = $args[0]

$stringMinuscula = $entrada.ToLower()
$stringModificada = $stringMinuscula.Replace(" ", "_")

# Caminho para o arquivo de URLs
$arquivoDeUrls = "C:/Users/souza/Downloads/urls.txt"

# Pasta onde as imagens serão salvas
$pastaDestino = "C:/Users/souza/Videos/VideoCreator/assets/imagens/"
if (!(Test-Path -Path $pastaDestino)) {
    New-Item -ItemType Directory -Path $pastaDestino | Out-Null
}

# Contador para nomear arquivos
$contador = 1

# Lê cada URL e faz o download
Get-Content $arquivoDeUrls | ForEach-Object {
    $url = $_.Trim()
    if ($url -ne "") {
        try {
            # Remove parâmetros (tudo após ? ou &)
            $urlLimpa = $url.Split('?')[0].Split('&')[0]

            # Extrai a extensão real (ex: .jpg, .png)
            $extensao = [System.IO.Path]::GetExtension($urlLimpa)
            if ([string]::IsNullOrEmpty($extensao)) {
                $extensao = ".jpg" # padrão se não tiver extensão
            }
 
            # Nome do arquivo (ex: imagem_1.jpg)
            $nomeArquivo = "$stringModificada$extensao"
            $caminhoCompleto = Join-Path $pastaDestino $nomeArquivo

            Invoke-WebRequest -Uri $url -OutFile $caminhoCompleto
            Write-Host "Baixado com sucesso! '$nomeArquivo'"
            @{ Path = $caminhoCompleto } | ConvertTo-Json -Compress
            $contador++
        } catch {
            Write-Host "ERRO AO BAIXAR IMAGEM."
            @{ Path = 'None' } | ConvertTo-Json -Compress
        }
    }
}

Start-Sleep -Seconds 3