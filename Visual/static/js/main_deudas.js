document.addEventListener('DOMContentLoaded', () => {
  // 1) Datos de ejemplo
  const deudas = [
    { descripcion:"Crédito educativo", entidad:"ICETEX", valor:3500000, Valor_cuota:400000, cuotas:12, interes:1.2 },
    { descripcion:"Tarjeta de crédito", entidad:"Banco A", valor:1200000, Valor_cuota:300000, cuotas:6, interes:2.5 },
    { descripcion:"Hipoteca", entidad:"Banco y", valor:500000, Valor_cuota:50000, cuotas:6, interes:4.0 },
    { descripcion:"Crédito de Moto", entidad:"Davivienda", valor:1500000, Valor_cuota:100000, cuotas:3, interes:1.5 }
  ];

  // 2) Pinta la tabla
  const cuerpo = document.getElementById('tablaCuerpo');
  deudas.forEach(d => {
    const fila = document.createElement('tr');
    fila.innerHTML = `
      <td>${d.descripcion}</td>
      <td>${d.entidad}</td>
      <td>$${d.valor.toLocaleString()}</td>
      <td>$${d.Valor_cuota.toLocaleString()}</td>
      <td>${d.cuotas}</td>
      <td>${d.interes}%</td>
    `;
    cuerpo.appendChild(fila);
  });

  // 3) Prepara datos para Chart.js
  const etiquetas = deudas.map(d => d.descripcion);
  const valores   = deudas.map(d => d.valor);

  // 4) Lee color base de CSS
  const root = getComputedStyle(document.documentElement);
  const baseColor = root.getPropertyValue('--color-primario').trim() || '#2980B9';

  // 5) Genera paleta automática
  const paleta = generarTonosSimilares(baseColor, valores.length);

  // 6) Crea el gráfico
  new Chart(document.getElementById('pieDeudas'), {
    type: 'pie',
    data: {
      labels: etiquetas,
      datasets: [{
        data: valores,
        backgroundColor: paleta,
        borderColor: '#ffffff',
        borderWidth: 2
      }]
    },
    options: {
      responsive: true,
      plugins: { legend:{position:'bottom'} }
    }
  });
});
