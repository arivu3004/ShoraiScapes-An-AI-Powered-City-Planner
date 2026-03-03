/* ============= PLANNER PAGE SCRIPT ============= */

document.addEventListener('DOMContentLoaded', function() {
    const layoutForm = document.getElementById('layoutForm');
    
    if (layoutForm) {
        layoutForm.addEventListener('submit', handleLayoutGeneration);
    }

    // Add real-time recommendations
    const formInputs = layoutForm?.querySelectorAll('input, select');
    if (formInputs) {
        formInputs.forEach(input => {
            input.addEventListener('change', getQuickRecommendations);
        });
    }
});

async function handleLayoutGeneration(e) {
    e.preventDefault();

    // Collect form data
    const population = document.getElementById('population').value;
    const temperature = document.getElementById('temperature').value;
    const weather = document.getElementById('weather').value;
    const roads = document.getElementById('roads').value;
    const city = document.getElementById('city').value;
    const total_area = document.getElementById('total_area').value;
    const shape = document.getElementById('shape').value;

    // Validate
    if (!population || !temperature || !weather || !roads || !city || !total_area || !shape) {
        showMessage('', 'Please fill in all fields', 'error');
        return;
    }

    // Show loading state
    const loadingSpinner = document.getElementById('loadingSpinner');
    const outputContainer = document.getElementById('outputContainer');
    const placeholderContent = document.getElementById('placeholderContent');

    loadingSpinner.style.display = 'flex';
    outputContainer.style.display = 'none';
    placeholderContent.style.display = 'none';

    try {
        // Call API
        const response = await apiCall('/api/generate-layout', 'POST', {
            population: population,
            temperature: temperature,
            weather: weather,
            roads: roads,
            city: city,
            total_area: total_area,
            shape: shape
        });

        if (response.success) {
            // Display results
            displayLayoutResults(response);
            outputContainer.style.display = 'block';
            loadingSpinner.style.display = 'none';
        } else {
            throw new Error(response.error || 'Failed to generate layout');
        }
    } catch (error) {
        console.error('Error:', error);
        loadingSpinner.style.display = 'none';
        placeholderContent.style.display = 'block';
        showMessage('', 'Error generating layout. Please try again.', 'error');
    }
}

function displayLayoutResults(response) {
    const report = response.report;

    // Display image
    const layoutImage = document.getElementById('layoutImage');
    layoutImage.src = response.layout_image;

    // Update report
    document.getElementById('reportPopulation').textContent = report.population;
    document.getElementById('reportDensity').textContent = report.density;
    document.getElementById('reportTemperature').textContent = report.temperature;
    document.getElementById('reportWeather').textContent = report.weather;
    document.getElementById('reportRoadWidth').textContent = report.road_width;
    document.getElementById('reportRoadDescription').textContent = report.road_description;
    document.getElementById('reportTimestamp').textContent = report.timestamp;

    // Display city information
    document.getElementById('reportCity').textContent = report.city;
    document.getElementById('reportArea').textContent = report.total_area;
    document.getElementById('reportShape').textContent = report.shape;

    // Display zone distribution
    if (report.zone_distribution) {
        const zoneDistDiv = document.getElementById('zoneDistribution');
        zoneDistDiv.innerHTML = '';
        
        for (const [zoneName, percentage] of Object.entries(report.zone_distribution)) {
            const zoneItem = document.createElement('div');
            zoneItem.style.cssText = 'margin: 10px 0; padding: 8px; background: #f5f5f5; border-radius: 4px; display: flex; justify-content: space-between; align-items: center;';
            
            const nameSpan = document.createElement('span');
            nameSpan.textContent = zoneName;
            nameSpan.style.fontWeight = '500';
            
            const percentSpan = document.createElement('span');
            percentSpan.textContent = percentage + '%';
            percentSpan.style.cssText = 'font-weight: bold; color: #2196F3; font-size: 1.1em;';
            
            const progressBar = document.createElement('div');
            progressBar.style.cssText = 'flex: 1; height: 20px; background: #ddd; border-radius: 3px; margin: 0 10px; overflow: hidden;';
            
            const progressFill = document.createElement('div');
            progressFill.style.cssText = `height: 100%; background: linear-gradient(to right, #2196F3, #4CAF50); width: ${percentage}%; transition: width 0.3s ease;`;
            progressBar.appendChild(progressFill);
            
            zoneItem.appendChild(nameSpan);
            zoneItem.appendChild(progressBar);
            zoneItem.appendChild(percentSpan);
            zoneDistDiv.appendChild(zoneItem);
        }
    }

    // Display budget information
    if (report.budget) {
        document.getElementById('reportBudget').textContent = report.budget.total_billions;
        document.getElementById('reportBudgetDetails').innerHTML = `
            <strong>Total:</strong> ${report.budget.total_millions}<br>
            <strong>Cost per km²:</strong> ${report.budget.cost_per_sqkm}
        `;
    }

    // Display amenities
    const amenitiesList = document.getElementById('reportAmenities');
    amenitiesList.innerHTML = '';
    report.amenities.forEach(amenity => {
        const li = document.createElement('li');
        li.textContent = amenity;
        amenitiesList.appendChild(li);
    });

    // Display recommendations
    const recommendationsList = document.getElementById('reportRecommendations');
    recommendationsList.innerHTML = '';
    report.recommendations.forEach(rec => {
        const li = document.createElement('li');
        li.textContent = rec;
        recommendationsList.appendChild(li);
    });
}

async function getQuickRecommendations() {
    const population = document.getElementById('population').value;
    const temperature = document.getElementById('temperature').value;
    const weather = document.getElementById('weather').value;
    const roads = document.getElementById('roads').value;
    const city = document.getElementById('city').value;
    const total_area = document.getElementById('total_area').value;
    const shape = document.getElementById('shape').value;

    if (population && temperature && weather && city && total_area && shape) {
        try {
            const response = await apiCall('/api/get-recommendations', 'POST', {
                population: population,
                temperature: temperature,
                weather: weather,
                roads: roads,
                city: city,
                total_area: total_area,
                shape: shape
            });

            // Show quick stats
            const quickStats = document.getElementById('quickStats');
            quickStats.style.display = 'block';

            document.getElementById('densityLevel').textContent = response.density;
            document.getElementById('roadWidth').textContent = `Level ${response.road_width}/4`;
            document.getElementById('amenitiesCount').textContent = response.amenities.length;
            document.getElementById('budgetEstimate').textContent = `$${response.budget_billions.toFixed(3)}B`;
        } catch (error) {
            console.error('Error getting recommendations:', error);
        }
    }
}
