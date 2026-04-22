<script lang="ts">
	import { onMount, onDestroy } from 'svelte';

	let visible = false;
	onMount(() => {
		visible = true;
		document.body.classList.add('arch-dark');
	});
	onDestroy(() => {
		document.body.classList.remove('arch-dark');
	});

	const stack = [
		{
			layer: 'Client',
			color: '#5B8FF9',
			accent: '#EBF1FF',
			items: [
				{ label: 'React + Vite SPA', detail: 'TypeScript, no SSR' },
				{ label: 'Apollo Client', detail: 'GraphQL data layer' },
				{ label: 'GraphQL Codegen', detail: 'End-to-end type safety' },
				{ label: 'shadcn/ui + Tailwind', detail: 'Component library' },
				{ label: 'Recharts', detail: 'Price & CMC charts' }
			]
		},
		{
			layer: 'API',
			color: '#5AD8A6',
			accent: '#E8FAF3',
			items: [
				{ label: 'FastAPI', detail: 'Python, port 8000 (internal)' },
				{ label: 'Strawberry GraphQL', detail: 'Schema + resolvers' },
				{ label: 'Better Auth JWT', detail: 'Validates incoming tokens' }
			]
		},
		{
			layer: 'Background Jobs',
			color: '#F6BD16',
			accent: '#FEF8E3',
			items: [
				{ label: 'Celery Worker', detail: 'Async task execution' },
				{ label: 'Celery Beat', detail: 'Cron-style scheduler' },
				{ label: 'Redis', detail: 'Broker + result backend' }
			]
		},
		{
			layer: 'Database',
			color: '#E86452',
			accent: '#FDECEA',
			items: [
				{ label: 'PostgreSQL 16', detail: 'Primary data store' },
				{ label: 'SQLAlchemy 2.0 async', detail: 'asyncpg driver' },
				{ label: 'Alembic', detail: 'Sole migration owner' }
			]
		}
	];

	const tables = [
		{
			name: 'cards',
			note: 'Read-only Scryfall cache. ~30k rows.',
			cols: [
				'id (scryfall uuid)',
				'name',
				'set_code',
				'mana_cost',
				'cmc',
				'color_identity[]',
				'price_usd (cents)',
				'price_usd_foil (cents)',
				'scryfall_data (jsonb)'
			]
		},
		{
			name: 'collection',
			note: 'User-owned card instances.',
			cols: [
				'id',
				'scryfall_id → cards',
				'quantity',
				'foil',
				'condition',
				'language',
				'purchase_price_cents'
			]
		},
		{
			name: 'decks',
			note: 'Deck metadata.',
			cols: ['id', 'name', 'format', 'description', 'commander_id → cards']
		},
		{
			name: 'deck_cards',
			note: 'Cards inside a deck.',
			cols: [
				'id',
				'deck_id → decks',
				'scryfall_id → cards',
				'quantity',
				'board',
				'categories[]',
				'foil'
			]
		},
		{
			name: 'price_history',
			note: 'Daily snapshots. INSERT ON CONFLICT DO NOTHING.',
			cols: [
				'id',
				'scryfall_id → cards',
				'price_usd (cents)',
				'price_usd_foil (cents)',
				'snapshot_date (YYYY-MM-DD)'
			]
		},
		{
			name: 'edhrec_cache',
			note: 'TTL = 7 days. Unofficial API buffer.',
			cols: ['id', 'slug (unique)', 'data (jsonb)', 'expires_at']
		}
	];

	const services = [
		{
			name: 'scryfall_sync.py',
			schedule: 'Every 24h via Celery Beat',
			desc: 'Fetches default_cards bulk JSON (~100MB). Batch upserts 500 cards at a time. Never hardcode the download URL — always fetch the metadata endpoint first.',
			tag: 'sync'
		},
		{
			name: 'price_snapshot.py',
			schedule: 'Every 24h via Celery Beat',
			desc: 'Reads distinct scryfall_ids from collection, joins to current prices in cards table, inserts into price_history. Uses ON CONFLICT DO NOTHING to avoid duplicate daily rows.',
			tag: 'snapshot'
		},
		{
			name: 'converter.py',
			schedule: 'On-demand (GraphQL mutation)',
			desc: 'Pivot pattern: every format goes through CanonicalCard. N parsers + N serializers, not N². Supports manabox ↔ moxfield ↔ archidekt. scryfall_id is the universal key.',
			tag: 'convert'
		},
		{
			name: 'edhrec.py',
			schedule: 'On-demand, cache-first',
			desc: 'Checks edhrec_cache (7d TTL) before fetching. Parsing isolated in _parse_recommendations() adapter. Always returns [] on parse failure — never crash on schema change.',
			tag: 'fragile'
		}
	];

	const principles = [
		{
			icon: '🔑',
			title: 'scryfall_id is the pivot key',
			body: 'Every card across every format (Manabox, Moxfield, Archidekt) is identified by its Scryfall UUID. Never rely on name+set as primary key — use name+set as fallback only for older Archidekt exports.'
		},
		{
			icon: '💰',
			title: 'Prices are always integer cents',
			body: 'Never store price as Float. Floating-point rounding corrupts price history. Convert on ingest: round(float(val) * 100). Display by dividing by 100 in the UI.'
		},
		{
			icon: '🏛️',
			title: 'Alembic owns all migrations',
			body: 'No other tool touches the schema. Run alembic revision --autogenerate, review the generated file, then alembic upgrade head. This was an explicit clean-slate decision.'
		},
		{
			icon: '🚫',
			title: 'N+1 prevention',
			body: 'Always use selectinload() in SQLAlchemy for relationship queries inside resolvers. Never lazy-load inside a loop.'
		},
		{
			icon: '🔒',
			title: 'Port exposure',
			body: 'Only port 3000 is exposed externally via Tailscale. FastAPI runs on port 8000, internal to Docker only. The client talks to GraphQL; nothing else is public.'
		},
		{
			icon: '⚠️',
			title: 'EDHRec is unofficial and fragile',
			body: 'JSON structure has changed before. All parsing lives in one adapter function. Always wrap in try/except and return [] on failure. Price tracking is limited to ~24h granularity via Scryfall — no real-time option.'
		}
	];

	const formats = [
		{
			name: 'Manabox',
			field: 'Scryfall ID',
			foil: '"foil" string',
			condition: 'Near Mint / Lightly Played …'
		},
		{
			name: 'Moxfield',
			field: 'Scryfall ID',
			foil: '"foil" / "etched"',
			condition: 'NM / LP / MP …'
		},
		{ name: 'Archidekt', field: 'scryfall_id', foil: '"true"/"false"', condition: 'NM / LP / MP …' }
	];

	let activeTable = tables[0].name;
</script>

<div class="arch">
	<!-- Header -->
	<div class="header" class:in={visible}>
		<div class="eyebrow">Architecture Reference</div>
		<h1>MTG App — v2</h1>
		<p class="subtitle">
			Python GraphQL backend · React TypeScript SPA · Self-hosted via Tailscale on Framework
			mainboard Linux server.
		</p>
		<div class="version">v2 · GraphQL + Python · April 2026</div>
	</div>

	<!-- Stack Overview -->
	<div class="section" class:in={visible} style="transition-delay: 0.08s">
		<div class="section-label">Stack Overview</div>
		<div class="stack-grid">
			{#each stack as layer}
				<div class="stack-col">
					<div class="stack-layer">
						<span class="stack-dot" style="background: {layer.color}"></span>
						{layer.layer}
					</div>
					{#each layer.items as item}
						<div class="stack-item">
							<div class="stack-item-label">{item.label}</div>
							<div class="stack-item-detail">{item.detail}</div>
						</div>
					{/each}
				</div>
			{/each}
		</div>
	</div>

	<!-- Request Flow -->
	<div class="section" class:in={visible} style="transition-delay: 0.14s">
		<div class="section-label">Request Flow</div>
		<div class="flow">
			<div class="flow-node">
				<div class="flow-node-label">Client</div>
				<div class="flow-node-name">React SPA</div>
				<div class="flow-node-detail">localhost:5173 / :3000</div>
			</div>
			<div class="flow-node">
				<div class="flow-node-label">Auth</div>
				<div class="flow-node-name">Better Auth</div>
				<div class="flow-node-detail">Session → JWT</div>
			</div>
			<div class="flow-node">
				<div class="flow-node-label">API</div>
				<div class="flow-node-name">FastAPI + Strawberry</div>
				<div class="flow-node-detail">:8000/graphql (internal)</div>
			</div>
			<div class="flow-node">
				<div class="flow-node-label">ORM</div>
				<div class="flow-node-name">SQLAlchemy 2.0 async</div>
				<div class="flow-node-detail">asyncpg driver</div>
			</div>
			<div class="flow-node">
				<div class="flow-node-label">Database</div>
				<div class="flow-node-name">PostgreSQL 16</div>
				<div class="flow-node-detail">:5432 via Docker</div>
			</div>
		</div>
	</div>

	<!-- Data Model -->
	<div class="section" class:in={visible} style="transition-delay: 0.2s">
		<div class="section-label">Data Model</div>
		<div class="table-tabs">
			{#each tables as t}
				<button
					class="tab-btn"
					class:active={activeTable === t.name}
					on:click={() => (activeTable = t.name)}>{t.name}</button
				>
			{/each}
		</div>
		{#each tables as t}
			{#if activeTable === t.name}
				<div class="table-panel">
					<div class="table-name">{t.name}</div>
					<div class="table-note">{t.note}</div>
					<div class="col-list">
						{#each t.cols as col}
							<div class="col-row">
								{#if col.includes('→')}
									<span class="fk">{col}</span>
								{:else if col.includes('cents') || col.includes('YYYY')}
									{col.split('(')[0].trim()}<span class="note">
										({col.split('(')[1]?.replace(')', '')})</span
									>
								{:else}
									{col}
								{/if}
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/each}
	</div>

	<!-- Background Services -->
	<div class="section" class:in={visible} style="transition-delay: 0.26s">
		<div class="section-label">Background Services</div>
		<div class="services-grid">
			{#each services as svc}
				<div class="service-card">
					<div class="service-header">
						<span class="service-name">{svc.name}</span>
						<span class="service-tag {svc.tag}">{svc.tag}</span>
					</div>
					<div class="service-schedule">{svc.schedule}</div>
					<div class="service-desc">{svc.desc}</div>
				</div>
			{/each}
		</div>
	</div>

	<!-- Converter Formats -->
	<div class="section" class:in={visible} style="transition-delay: 0.32s">
		<div class="section-label">Converter Formats</div>
		<table class="formats-table">
			<thead>
				<tr>
					<th>Format</th>
					<th>ID field</th>
					<th>Foil field</th>
					<th>Condition values</th>
				</tr>
			</thead>
			<tbody>
				{#each formats as fmt}
					<tr>
						<td>{fmt.name}</td>
						<td>{fmt.field}</td>
						<td>{fmt.foil}</td>
						<td>{fmt.condition}</td>
					</tr>
				{/each}
			</tbody>
		</table>
		<div class="pivot-note">
			<strong>Pivot pattern:</strong> All conversions go through <code>CanonicalCard</code>. Never
			convert A→B directly — always A→canonical→B. This gives N adapters instead of N² converters.
			Older Archidekt exports may be missing <code>scryfall_id</code> — fall back to name+set lookup against
			the cards table.
		</div>
	</div>

	<!-- Key Principles -->
	<div class="section" class:in={visible} style="transition-delay: 0.38s">
		<div class="section-label">Key Principles & Gotchas</div>
		<div class="principles-grid">
			{#each principles as p}
				<div class="principle">
					<div class="principle-icon">{p.icon}</div>
					<div class="principle-title">{p.title}</div>
					<div class="principle-body">{p.body}</div>
				</div>
			{/each}
		</div>
	</div>
</div>

<style>
	:global(body.arch-dark) {
		margin: 0;
		background: #0f0f0f;
	}

	.arch {
		font-family: 'IBM Plex Mono', 'JetBrains Mono', 'Fira Code', monospace;
		background: #0f0f0f;
		color: #e8e6df;
		min-height: 100vh;
		padding: 3rem 1.5rem;
	}

	.arch * {
		box-sizing: border-box;
	}

	/* Header */
	.header {
		max-width: 900px;
		margin: 0 auto 3rem;
		opacity: 0;
		transform: translateY(16px);
		transition:
			opacity 0.5s ease,
			transform 0.5s ease;
	}
	.header.in {
		opacity: 1;
		transform: none;
	}

	.eyebrow {
		font-size: 10px;
		letter-spacing: 0.2em;
		text-transform: uppercase;
		color: #5ad8a6;
		margin-bottom: 0.5rem;
	}
	h1 {
		font-size: clamp(1.6rem, 4vw, 2.4rem);
		font-weight: 400;
		color: #f0ede6;
		margin: 0 0 0.5rem;
		letter-spacing: -0.02em;
		line-height: 1.15;
	}
	.subtitle {
		font-size: 13px;
		color: #7a7870;
		line-height: 1.7;
		max-width: 560px;
	}
	.version {
		display: inline-block;
		font-size: 10px;
		background: #1a1a1a;
		border: 1px solid #2a2a2a;
		color: #5b8ff9;
		padding: 3px 8px;
		border-radius: 3px;
		margin-top: 0.75rem;
	}

	/* Sections */
	.section {
		max-width: 900px;
		margin: 0 auto 3rem;
		opacity: 0;
		transform: translateY(12px);
		transition:
			opacity 0.5s ease,
			transform 0.5s ease;
	}
	.section.in {
		opacity: 1;
		transform: none;
	}

	.section-label {
		font-size: 10px;
		letter-spacing: 0.18em;
		text-transform: uppercase;
		color: #4a4a48;
		margin-bottom: 1rem;
		padding-bottom: 0.5rem;
		border-bottom: 1px solid #1e1e1c;
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.section-label::before {
		content: '';
		display: inline-block;
		width: 3px;
		height: 12px;
		background: #5ad8a6;
		border-radius: 1px;
		flex-shrink: 0;
	}

	/* Stack grid */
	.stack-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
		gap: 1px;
		background: #1e1e1c;
		border: 1px solid #1e1e1c;
		border-radius: 8px;
		overflow: hidden;
	}

	.stack-col {
		background: #141412;
		padding: 1.25rem;
	}

	.stack-layer {
		font-size: 9px;
		letter-spacing: 0.15em;
		text-transform: uppercase;
		font-weight: 600;
		margin-bottom: 0.75rem;
		display: flex;
		align-items: center;
		gap: 6px;
	}
	.stack-dot {
		width: 6px;
		height: 6px;
		border-radius: 50%;
		flex-shrink: 0;
	}

	.stack-item {
		margin-bottom: 0.6rem;
	}
	.stack-item-label {
		font-size: 12px;
		color: #d4d0c8;
		line-height: 1.3;
	}
	.stack-item-detail {
		font-size: 10px;
		color: #5a5a56;
		margin-top: 1px;
	}

	/* Data model */
	.table-tabs {
		display: flex;
		flex-wrap: wrap;
		gap: 4px;
		margin-bottom: 1px;
	}
	.tab-btn {
		background: #141412;
		border: 1px solid #2a2a28;
		color: #7a7870;
		font-family: inherit;
		font-size: 11px;
		padding: 5px 10px;
		border-radius: 4px;
		cursor: pointer;
		transition: all 0.15s;
	}
	.tab-btn:hover {
		color: #d4d0c8;
		border-color: #3a3a38;
	}
	.tab-btn.active {
		background: #1e1e1c;
		color: #5ad8a6;
		border-color: #5ad8a6;
	}

	.table-panel {
		background: #141412;
		border: 1px solid #2a2a28;
		border-radius: 0 6px 6px 6px;
		padding: 1.25rem;
	}
	.table-name {
		font-size: 14px;
		color: #5ad8a6;
		margin-bottom: 0.25rem;
	}
	.table-note {
		font-size: 11px;
		color: #5a5a56;
		margin-bottom: 1rem;
	}
	.col-list {
		display: flex;
		flex-direction: column;
		gap: 3px;
	}
	.col-row {
		font-size: 11.5px;
		color: #c8c4bc;
		display: flex;
		align-items: center;
		gap: 8px;
	}
	.col-row::before {
		content: '—';
		color: #3a3a38;
		flex-shrink: 0;
	}
	.col-row .fk {
		color: #5b8ff9;
	}
	.col-row .note {
		color: #4a4a48;
		font-size: 10px;
	}

	/* Services */
	.services-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(380px, 1fr));
		gap: 1px;
		background: #1e1e1c;
		border: 1px solid #1e1e1c;
		border-radius: 8px;
		overflow: hidden;
	}
	.service-card {
		background: #141412;
		padding: 1.25rem;
	}
	.service-header {
		display: flex;
		align-items: flex-start;
		justify-content: space-between;
		margin-bottom: 0.4rem;
		gap: 8px;
	}
	.service-name {
		font-size: 13px;
		color: #d4d0c8;
	}
	.service-tag {
		font-size: 9px;
		letter-spacing: 0.1em;
		text-transform: uppercase;
		padding: 2px 7px;
		border-radius: 3px;
		flex-shrink: 0;
	}
	.service-tag.sync {
		background: #0a2a20;
		color: #5ad8a6;
	}
	.service-tag.snapshot {
		background: #0a1f35;
		color: #5b8ff9;
	}
	.service-tag.convert {
		background: #2a1f05;
		color: #f6bd16;
	}
	.service-tag.fragile {
		background: #2a0a08;
		color: #e86452;
	}

	.service-schedule {
		font-size: 10px;
		color: #5a5a56;
		margin-bottom: 0.6rem;
	}
	.service-desc {
		font-size: 11.5px;
		color: #7a7870;
		line-height: 1.65;
	}

	/* Converter formats */
	.formats-table {
		width: 100%;
		border-collapse: collapse;
		font-size: 12px;
	}
	.formats-table th {
		text-align: left;
		font-size: 9px;
		letter-spacing: 0.15em;
		text-transform: uppercase;
		color: #4a4a48;
		padding: 0 12px 8px 0;
		border-bottom: 1px solid #1e1e1c;
		font-weight: 400;
	}
	.formats-table td {
		padding: 8px 12px 8px 0;
		color: #c8c4bc;
		border-bottom: 1px solid #1a1a18;
		vertical-align: top;
	}
	.formats-table td:first-child {
		color: #5ad8a6;
	}
	.formats-table tr:last-child td {
		border-bottom: none;
	}

	.pivot-note {
		margin-top: 1rem;
		background: #141412;
		border: 1px solid #2a2a28;
		border-left: 3px solid #f6bd16;
		padding: 0.75rem 1rem;
		border-radius: 0 5px 5px 0;
		font-size: 11.5px;
		color: #7a7870;
		line-height: 1.65;
	}
	.pivot-note strong {
		color: #f6bd16;
	}

	/* Principles */
	.principles-grid {
		display: grid;
		grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
		gap: 1px;
		background: #1e1e1c;
		border: 1px solid #1e1e1c;
		border-radius: 8px;
		overflow: hidden;
	}
	.principle {
		background: #141412;
		padding: 1.25rem;
	}
	.principle-icon {
		font-size: 18px;
		margin-bottom: 0.5rem;
	}
	.principle-title {
		font-size: 12px;
		color: #d4d0c8;
		margin-bottom: 0.4rem;
		line-height: 1.3;
	}
	.principle-body {
		font-size: 11px;
		color: #5a5a56;
		line-height: 1.7;
	}

	/* Data flow diagram */
	.flow {
		display: flex;
		align-items: center;
		flex-wrap: wrap;
		gap: 0;
		background: #141412;
		border: 1px solid #2a2a28;
		border-radius: 8px;
		overflow: hidden;
		font-size: 11px;
	}
	.flow-node {
		padding: 0.9rem 1.1rem;
		line-height: 1.4;
		flex: 1;
		min-width: 120px;
		border-right: 1px solid #1e1e1c;
		position: relative;
	}
	.flow-node:last-child {
		border-right: none;
	}
	.flow-node-label {
		color: #7a7870;
		font-size: 9px;
		letter-spacing: 0.12em;
		text-transform: uppercase;
		margin-bottom: 3px;
	}
	.flow-node-name {
		color: #d4d0c8;
		font-size: 12px;
	}
	.flow-node-detail {
		color: #4a4a48;
		font-size: 10px;
		margin-top: 2px;
	}
	.flow-arrow {
		padding: 0 0.5rem;
		color: #3a3a38;
		font-size: 14px;
		flex-shrink: 0;
	}

	@media (max-width: 640px) {
		.stack-grid {
			grid-template-columns: 1fr 1fr;
		}
		.services-grid {
			grid-template-columns: 1fr;
		}
		.principles-grid {
			grid-template-columns: 1fr;
		}
		.flow {
			flex-direction: column;
		}
		.flow-node {
			border-right: none;
			border-bottom: 1px solid #1e1e1c;
			width: 100%;
		}
		.flow-node:last-child {
			border-bottom: none;
		}
	}
</style>
