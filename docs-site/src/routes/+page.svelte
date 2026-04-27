<svelte:head>
	<title>MTG App Dev Notes Home</title>
</svelte:head>

<script lang="ts">
    import { resolve } from '$app/paths';
</script>

<div class="mx-auto max-w-3xl px-4 py-16">
	<h1 class="mb-4 text-4xl font-bold">MTG App Dev Notes</h1>
	<p class="mb-8 text-lg text-slate-600 dark:text-slate-400">
		Build logs and architecture docs for a self-hosted MTG collection manager.
	</p>
	<ul class="space-y-3">
		<li><a href={resolve("/build-guide")} class="text-blue-600 hover:underline">Build guided (revisions) →</a></li>
		<li><a href={resolve("/docs/architecture")} class="text-blue-600 hover:underline">Architecture →</a></li>
		<li><a href={resolve("/docs/stack")} class="text-blue-600 hover:underline">Stack and Reference →</a></li>
		<li><a href={resolve("/docs/erd")} class="text-blue-600 hover:underline">ERD Chart (Mermaid) →</a></li>
	</ul>
	<p class="mt-8 mb-4 text-lg text-slate-600 dark:text-slate-400">Development Journal</p>
	<ul class="space-y-3">
		<li><a href={resolve("/journal")} class="text-blue-600 hover:underline">Entry 1 (XX-XX-XXXX) →</a></li>
	</ul>
</div>
