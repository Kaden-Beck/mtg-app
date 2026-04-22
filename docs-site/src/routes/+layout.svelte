<script lang="ts">
	import './layout.css';
	import favicon from '$lib/assets/favicon.svg';

	let { children } = $props();
</script>

<svelte:head><link rel="icon" href={favicon} /></svelte:head>

<nav class="border-b border-slate-200 bg-white px-4 py-3">
	<a href="/" class="font-mono text-sm text-slate-500 hover:text-slate-900">
		← home
	</a>
</nav>

{@render children()}
