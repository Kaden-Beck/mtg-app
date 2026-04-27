<script lang="ts">
    import { resolve } from '$app/paths';
    import type { LayoutProps } from './$types';

    let { children }: LayoutProps = $props();
</script>

{@render children()}
<footer>
    <a href={resolve('/build-guide')}>Go back to Revisions</a>
</footer>