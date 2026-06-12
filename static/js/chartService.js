// chartService.js: Manages the creation and updating of all charts on the dashboard.
//
// This module provides functions for generating various types of charts (doughnut, bar)
// using the Chart.js library. It encapsulates the logic for preparing chart data,
// configuring chart options, and ensuring proper rendering on the canvas elements.
//
// Key Aspects:
// - Centralized functions for creating and updating different chart types.
// - Handles clearing existing charts on a canvas before drawing new ones to prevent conflicts.
// - Configures Chart.js options for visual presentation, including data labels and legends.
//
// Dependencies:
// - Chart.js (external library for charting)
//
// Key Functions:
// - updateChart(): Updates an existing Chart.js instance with new data.
// - destroyChart(): Destroys a Chart.js instance to free up resources.
// - ensureCanvasClear(): Ensures a canvas is ready for a new chart.
// - createDeviceChart(): Creates a doughnut chart for device user distribution.
// - createTrafficSourceChart(): Creates a bar chart for traffic source distribution.
// - createRankingChangeDistributionChart(): Creates a bar chart for keyword ranking change distribution.

/**
 * Chart.js 인스턴스를 업데이트합니다. 인스턴스가 없으면 아무 작업도 하지 않습니다.
 * @param {Chart} chartInstance - 업데이트할 차트 인스턴스
 * @param {string[]} labels - 새로운 레이블 배열
 * @param {object[]} datasets - 새로운 데이터셋 배열
 */
export function updateChart(chartInstance, labels, datasets) {
  if (!chartInstance) return;
  chartInstance.data.labels = labels;
  chartInstance.data.datasets = datasets;
  chartInstance.update();
}

/**
 * Chart.js 인스턴스를 파괴합니다.
 * @param {Chart} chartInstance - 파괴할 차트 인스턴스
 * @returns {null} 항상 null을 반환하여 이전 변수를 초기화하는 데 사용할 수 있습니다.
 */
export function destroyChart(chartInstance) {
  if (chartInstance) {
    chartInstance.destroy();
  }
  return null;
}

/**
 * 캔버스가 새 차트 생성을 위해 준비되었는지 확인하고, 기존 차트가 있다면 파괴합니다.
 * @param {HTMLCanvasElement} canvasElement - 확인할 캔버스 요소.
 */
function ensureCanvasClear(canvasElement) {
  const existingChart = Chart.getChart(canvasElement);
  if (existingChart) {
    existingChart.destroy();
    console.log(`Destroyed existing chart on canvas: ${canvasElement.id}`);
  }
}

/**
 * 기기별 사용자 분포를 보여주는 도넛 차트를 생성합니다.
 * @param {CanvasRenderingContext2D} ctx - 그림을 그릴 캔버스 렌더링 컨텍스트
 * @param {object} deviceUsers - { mobile, desktop, tablet } 형태의 데이터 객체
 * @returns {Chart} 새로 생성된 Chart.js 인스턴스
 */
export function createDeviceChart(ctx, deviceUsers) {
  const canvasElement = ctx.canvas;
  ensureCanvasClear(canvasElement);

  return new Chart(ctx, {
    type: "doughnut",
    data: {
      labels: ["Mobile", "Desktop", "Tablet"],
      datasets: [
        {
          label: "Users by Device",
          data: [
            deviceUsers.mobile || 0,
            deviceUsers.desktop || 0,
            deviceUsers.tablet || 0,
          ],
          backgroundColor: ["#4F46E5", "#3B82F6", "#10B981"],
          hoverOffset: 30,
        },
      ],
    },
    options: {
      plugins: {
        datalabels: {
          color: "#fff",
          formatter: (value) => value.toLocaleString(),
        },
        legend: {
          position: "bottom",
          labels: {
            font: {
              size: 14,
            },
          },
        },
      },
    },
  });
}

/**
 * 트래픽 소스별 분포를 보여주는 바 차트를 생성합니다.
 * @param {CanvasRenderingContext2D} ctx - 그림을 그릴 캔버스 렌더링 컨텍스트
 * @param {object} trafficSources - { search, referral, direct, social } 형태의 데이터 객체
 * @returns {Chart} 새로 생성된 Chart.js 인스턴스
 */
export function createTrafficSourceChart(ctx, trafficSources) {
  const canvasElement = ctx.canvas;
  ensureCanvasClear(canvasElement);

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Search", "Referral", "Direct", "Social"],
      datasets: [
        {
          label: "Traffic Sources",
          data: [
            trafficSources.search || 0,
            trafficSources.referral || 0,
            trafficSources.direct || 0,
            trafficSources.social || 0,
          ],
          backgroundColor: ["#2563EB", "#4B5563", "#F59E0B", "#9333EA"],
        },
      ],
    },
    options: {
      plugins: {
        datalabels: {
          anchor: "end",
          align: "top",
          color: "#000",
          font: {
            weight: "bold",
          },
          formatter: (value) => value.toLocaleString(),
        },
        legend: {
          display: false,
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            stepSize: 1,
          },
        },
      },
    },
  });
}

/**
 * Creates a doughnut chart showing keyword ranking change distribution.
 * @param {CanvasRenderingContext2D} ctx - The canvas rendering context to draw on.
 * @param {object} distribution - Data object in the form { up, down, new, unchanged }.
 * @returns {Chart} The newly created Chart.js instance.
 */
export function createRankingChangeDistributionChart(ctx, distribution) {
  const canvasElement = ctx.canvas;
  ensureCanvasClear(canvasElement);

  return new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Up", "Down", "New", "Unchanged"],
      datasets: [
        {
          label: "Keyword Rank Changes",
          data: [
            distribution.up || 0,
            distribution.down || 0,
            distribution.new || 0,
            distribution.unchanged || 0,
          ],
          backgroundColor: ["#34D399", "#A78BFA", "#60A5FA", "#D1D5DB"],
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        datalabels: {
          color: "#fff",
          font: {
            weight: "bold",
          },
          formatter: (value) => value.toLocaleString(),
        },
        legend: {
          display: false,
        },
        title: {
          display: false,
          text: "Keyword Ranking Change Distribution",
          font: {
            size: 16,
          },
        },
      },
      scales: {
        y: {
          beginAtZero: true,
          ticks: {
            callback: function (value) {
              if (Number.isInteger(value)) {
                return value;
              }
            },
          },
        },
      },
    },
  });
}
