const API_BASE = "/api/reports/landings";

let paginaAtual = 1;
let totalPaginas = 1;
let graficoEspecies = null;
let graficoDatas = null;

document.addEventListener("DOMContentLoaded", () => {
    carregarDados(1);
});

function obterFiltros() {
    const params = new URLSearchParams();
    const dataInicio = document.getElementById("data_inicio").value;
    const dataFim = document.getElementById("data_fim").value;
    const embarcacao = document.getElementById("embarcacao").value.trim();
    const especie = document.getElementById("especie").value.trim();
    const porto = document.getElementById("porto").value.trim();
    const status = document.getElementById("status").value;

    if (dataInicio) params.append("data_inicio", dataInicio);
    if (dataFim) params.append("data_fim", dataFim);
    if (embarcacao) params.append("embarcacao", embarcacao);
    if (especie) params.append("especie", especie);
    if (porto) params.append("porto", porto);
    if (status) params.append("status", status);

    return params;
}

async function carregarDados(page = 1) {
    paginaAtual = page;
    const params = obterFiltros();
    params.append("page", paginaAtual);
    params.append("page_size", 20);

    const tbody = document.getElementById("tabela_dados");
    tbody.innerHTML = '<tr><td colspan="6" class="empty">Carregando registros...</td></tr>';

    try {
        const [listaResponse, resumoResponse] = await Promise.all([
            fetch(`${API_BASE}?${params.toString()}`),
            fetch(`/api/reports/landings/summary?${params.toString()}`)
        ]);

        if (!listaResponse.ok || !resumoResponse.ok) {
            throw new Error("Falha ao consultar os dados.");
        }

        const lista = await listaResponse.json();
        const resumo = await resumoResponse.json();

        atualizarTabela(lista);
        atualizarMetricas(resumo);
        atualizarGraficos(resumo);
    } catch (error) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">Não foi possível carregar os dados. Tente novamente.</td></tr>';
        console.error(error);
    }
}

function atualizarTabela(lista) {
    const tbody = document.getElementById("tabela_dados");

    if (!lista.items.length) {
        tbody.innerHTML = '<tr><td colspan="6" class="empty">Nenhum registro encontrado para os filtros selecionados.</td></tr>';
        document.getElementById("informacao_paginacao").textContent = "";
        return;
    }

    tbody.innerHTML = lista.items.map(item => `
        <tr>
            <td>${formatarData(item.landing_date)}</td>
            <td>${escaparHtml(item.vessel_name || "Não informado")}</td>
            <td>${escaparHtml(item.species || "Não informado")}</td>
            <td>${formatarNumero(item.weight_kg)} kg</td>
            <td>${escaparHtml(item.port || "Não informado")}</td>
            <td><span class="status">${escaparHtml(item.status || "Não informado")}</span></td>
        </tr>
    `).join("");

    totalPaginas = Math.max(1, Math.ceil(lista.total / lista.page_size));
    document.getElementById("informacao_paginacao").textContent =
        `Página ${lista.page} de ${totalPaginas} — ${lista.total} registro(s)`;
}

function atualizarMetricas(resumo) {
    document.getElementById("metrica_total").textContent = resumo.total_records;
    document.getElementById("metrica_peso").textContent = `${formatarNumero(resumo.total_weight_kg)} kg`;
    document.getElementById("metrica_media").textContent = `${formatarNumero(resumo.average_weight_kg)} kg`;
}

function atualizarGraficos(resumo) {
    const especies = resumo.by_species.slice(0, 10);
    const datas = resumo.by_date;

    if (graficoEspecies) graficoEspecies.destroy();
    if (graficoDatas) graficoDatas.destroy();

    graficoEspecies = new Chart(document.getElementById("grafico_especies"), {
        type: "bar",
        data: {
            labels: especies.map(item => item.label),
            datasets: [{ label: "Volume (kg)", data: especies.map(item => item.value), backgroundColor: "#0b5d7a" }]
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true } } }
    });

    graficoDatas = new Chart(document.getElementById("grafico_datas"), {
        type: "line",
        data: {
            labels: datas.map(item => item.label),
            datasets: [{ label: "Volume (kg)", data: datas.map(item => item.value), borderColor: "#0b5d7a", backgroundColor: "rgba(11,93,122,0.15)", fill: true, tension: 0.3 }]
        },
        options: { responsive: true, scales: { y: { beginAtZero: true } } }
    });
}

function mudarPagina(direcao) {
    const novaPagina = paginaAtual + direcao;
    if (novaPagina < 1 || novaPagina > totalPaginas) return;
    carregarDados(novaPagina);
}

function limparFiltros() {
    ["data_inicio", "data_fim", "embarcacao", "especie", "porto", "status"].forEach(id => {
        document.getElementById(id).value = "";
    });
    carregarDados(1);
}

async function exportarCSV() {
    const params = obterFiltros();
    params.append("page", 1);
    params.append("page_size", 100);

    try {
        const response = await fetch(`${API_BASE}?${params.toString()}`);
        if (!response.ok) throw new Error("Falha ao exportar os dados.");

        const data = await response.json();
        const cabecalho = ["Data", "Embarcacao", "Especie", "Peso (kg)", "Porto", "Status"];
        const linhas = data.items.map(item => [
            item.landing_date || "",
            item.vessel_name || "",
            item.species || "",
            item.weight_kg ?? "",
            item.port || "",
            item.status || ""
        ]);

        const csv = [cabecalho, ...linhas]
            .map(linha => linha.map(valor => `"${String(valor).replace(/"/g, '""')}"`).join(","))
            .join("\n");

        const blob = new Blob(["\uFEFF" + csv], { type: "text/csv;charset=utf-8;" });
        const link = document.createElement("a");
        link.href = URL.createObjectURL(blob);
        link.download = "descargas_atum.csv";
        link.click();
        URL.revokeObjectURL(link.href);
    } catch (error) {
        alert("Não foi possível exportar os dados.");
        console.error(error);
    }
}

function formatarData(valor) {
    if (!valor) return "Não informado";
    return new Date(valor).toLocaleDateString("pt-BR");
}

function formatarNumero(valor) {
    return Number(valor || 0).toLocaleString("pt-BR", { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

function escapar(valor) {
    const div = document.createElement("div");
    div.textContent = valor;
    return div.innerHTML;
}

function escaparHtml(valor) {
    return escapar(valor);
}
