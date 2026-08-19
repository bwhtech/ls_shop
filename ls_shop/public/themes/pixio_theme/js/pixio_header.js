/* Header chrome state: the mobile drawer, the mega-menu accordion, the search canvas and the
   cart drawer. Pixio's own jQuery stamps these state classes; this is the Alpine replacement.

   It has to be its own file rather than an addition to pixio.js: pixio.js is deferred at the
   end of the layout, by which point alpine:init has already fired and Alpine.data() would
   register a component nobody asks for again. */
document.addEventListener('alpine:init', () => {
	Alpine.data('pixio_header', () => ({
		menu_open: false,
		search_open: false,
		cart_open: false,
		cart_tab: 'cart',
		open_branches: [],
		cart_detail_loaded: false,
		bottom_bar_active: false,

		init() {
			/* Below 768px style.css parks .extra-nav off the bottom edge and slides it up on
			   .active, which upstream stamps from a jQuery scroll handler. A sentinel at the
			   header's bottom edge reads the same moment without running work per scroll frame. */
			const observer = new IntersectionObserver((entries) => {
				this.bottom_bar_active = !entries[0].isIntersecting;
			});
			observer.observe(this.$refs.header_sentinel);
		},

		is_branch_open(branch_key) {
			return this.open_branches.includes(branch_key);
		},

		toggle_branch(branch_key) {
			this.open_branches = this.is_branch_open(branch_key)
				? this.open_branches.filter((key) => key !== branch_key)
				: [...this.open_branches, branch_key];
		},

		async open_cart() {
			this.search_open = false;
			this.menu_open = false;
			this.cart_open = true;
			/* Stock and price are only stamped onto the persisted cart by an API read, and
			   increment() refuses to go past stock_qty - without this the stepper is dead on
			   any page that never loaded the cart itself. Once per page, on first open. */
			if (!this.cart_detail_loaded && Alpine.store('cart').items.length) {
				this.cart_detail_loaded = true;
				await Alpine.store('cart').fetch_detail_for_cart();
			}
		},

		open_search() {
			this.cart_open = false;
			this.menu_open = false;
			this.search_open = true;
		},

		open_mobile_menu() {
			this.search_open = false;
			this.cart_open = false;
			this.menu_open = true;
		},

		close_overlays() {
			this.menu_open = false;
			this.search_open = false;
			this.cart_open = false;
		},
	}));
});
