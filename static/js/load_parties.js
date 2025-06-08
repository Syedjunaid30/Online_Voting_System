async function fetchParties() {
    try {
        const res = await fetch('/api/votes_data');
        if (!res.ok) throw new Error('Failed to fetch');
        return await res.json();
    } catch (err) {
        console.error(err);
        return null;
    }
}

function createPartyCard(party) {
    const card = document.createElement('div');
    card.className = 'party-card';
    card.style.borderColor = party.color;

    card.innerHTML = `
        <img src="/static/party_logos/${party.logo}" class="party-logo" alt="Logo" />
        <div class="party-info">
            <div class="party-name">${party.name}</div>
            <div class="vote-count">${party.votes} votes</div>
        </div>
    `;
    return card;
}

async function loadParties() {
    const container = document.getElementById('resultsContainer');
    const data = await fetchParties();

    container.innerHTML = ''; // Clear skeletons

    if (!data || !data.names.length) {
        container.innerHTML = '<p style="color:red;text-align:center;">No parties found or failed to load data.</p>';
        return;
    }

    for (let i = 0; i < data.names.length; i++) {
        const party = {
            name: data.names[i],
            votes: data.votes[i],
            color: data.colors[i],
            logo: data.logos[i]
        };
        container.appendChild(createPartyCard(party));
    }
}

loadParties();
setInterval(loadParties, 10000); // Refresh every 10s
