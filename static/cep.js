const cep = document.getElementById("cep");
const statusCep = document.getElementById("cepStatus");
const address = document.getElementById("address");
document.getElementById("buscarCep").addEventListener("click", async () => {
    const value = cep.value.replace(/\D/g, "");
    if (!/^\d{8}$/.test(value)) {
        statusCep.textContent = "Informe um CEP com 8 números.";
        return;
    }
    statusCep.textContent = "Consultando...";
    try {
        const response = await fetch("https://viacep.com.br/ws/" + value + "/json/", {signal: AbortSignal.timeout(8000)});
        if (!response.ok) throw new Error();
        const data = await response.json();
        if (data.erro) {
            statusCep.textContent = "CEP não encontrado. Digite o endereço manualmente.";
            return;
        }
        if (cep.value.replace(/\D/g, "") !== value) return;
        address.value = [data.logradouro, data.bairro, data.localidade, data.uf, data.cep].filter(Boolean).join(", ");
        statusCep.textContent = "Confira o endereço e acrescente número e complemento.";
        address.focus();
    } catch {
        statusCep.textContent = "Consulta indisponível. Digite o endereço manualmente.";
    }
});
