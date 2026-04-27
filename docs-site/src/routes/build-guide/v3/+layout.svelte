<script lang="ts">
	import { resolve } from '$app/paths';
	import { page } from '$app/state';

	const PAGES = [
		{ href: resolve('/build-guide/v3'), label: 'Intro' },
		{ href: resolve('/build-guide/v3/part-1'), label: 'Part 1' },
		{ href: resolve('/build-guide/v3/part-2'), label: 'Part 2' },
		{ href: resolve('/build-guide/v3/part-3'), label: 'Part 3' },
		{ href: resolve('/build-guide/v3/part-4'), label: 'Part 4' },
		{ href: resolve('/build-guide/v3/part-5'), label: 'Part 5' },
		{ href: resolve('/build-guide/v3/part-6'), label: 'Part 6' },
		{ href: resolve('/build-guide/v3/part-7'), label: 'Part 7' },
	];

	let { children } = $props();

	let current = $derived(
		PAGES.findIndex(
			(p) => page.url.pathname === p.href || page.url.pathname === p.href + '/'
		)
	);

	let prev = $derived(current > 1 ? PAGES[current - 1] : null);
	let next = $derived(
		current === 0
			? PAGES[1]
			: current >= PAGES.length - 1
				? PAGES[1]
				: PAGES[current + 1]
	);
</script>

{@render children()}

<nav class="not-prose mt-12 border-t border-slate-200 pt-6 flex items-center justify-between text-sm font-mono">
	<span class="w-28">
		{#if prev}
			<a href={prev.href} class="text-slate-500 hover:text-slate-900">← {prev.label}</a>
		{/if}
	</span>

	<a href={resolve('/build-guide/v3')} class="text-slate-400 hover:text-slate-900">home</a>

	<span class="w-28 text-right">
		{#if next}
			<a href={next.href} class="text-slate-500 hover:text-slate-900">{next.label} →</a>
		{/if}
	</span>
</nav>
