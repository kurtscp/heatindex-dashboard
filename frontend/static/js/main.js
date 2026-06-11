/**
 * HeatWatch — Main Client-Side JavaScript
 * Handles shared utilities and page transitions.
 */

// Smooth page transition animation
document.addEventListener('DOMContentLoaded', function () {
    // Fade-in animation for page content
    const pageContainer = document.querySelector('.page-container');
    if (pageContainer) {
        pageContainer.style.opacity = '0';
        pageContainer.style.transform = 'translateY(8px)';
        pageContainer.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        requestAnimationFrame(() => {
            pageContainer.style.opacity = '1';
            pageContainer.style.transform = 'translateY(0)';
        });
    }

    // Animate metric cards on load with staggered delay
    const metricCards = document.querySelectorAll('.metric-card');
    metricCards.forEach((card, i) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(10px)';
        card.style.transition = `opacity 0.4s ease ${i * 0.08}s, transform 0.4s ease ${i * 0.08}s`;
        requestAnimationFrame(() => {
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        });
    });

    // Animate chart containers
    const chartContainers = document.querySelectorAll('.chart-container');
    chartContainers.forEach((chart, i) => {
        chart.style.opacity = '0';
        chart.style.transform = 'translateY(10px)';
        chart.style.transition = `opacity 0.5s ease ${0.3 + i * 0.1}s, transform 0.5s ease ${0.3 + i * 0.1}s`;
        requestAnimationFrame(() => {
            chart.style.opacity = '1';
            chart.style.transform = 'translateY(0)';
        });
    });
});
