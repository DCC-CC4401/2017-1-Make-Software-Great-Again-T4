sessionStorage = sessionStorage || {};
sessionStorage.filters = sessionStorage.filters || JSON.stringify({
        favoritesOnly: false,
        categoriesWhiteList: []
    });

function applyFilters(vendors) {
    const filters = JSON.parse(sessionStorage.filters);

    if (filters.favoritesOnly)
        vendors = vendors.filter(vendor => vendor.fav);

    /* "must include all categories" semantics
    if (filters.requiredCategories.length)
        for (const category of filters.requiredCategories)
            vendors = vendors.filter(vendor =>
                vendor.products.find(product =>
                    product.categories.includes(category) && product.stock)); */

    /* "must include one of the categories" semantics */
    if (filters.categoriesWhiteList.length) {
        let union = [];
        for (const category of filters.categoriesWhiteList)
            union = R.union(
                vendors.filter(vendor =>
                    vendor.products.find(product =>
                        product.categories.includes(category) && product.stock)),
                union);
        vendors = union;
    }

    return vendors;
}

function updateVendors() {
    const unfilteredVendors = window._unfilteredVendors || [];
    const vendors = applyFilters(unfilteredVendors);
    const showVendors = window._showVendors || (vendors => {/* pass */});
    showVendors(vendors);
}

$((/* on document ready */) => {
    const $favoritesOnly = $('#favorites-only');
    const $categoryFilter = $('.category-filter');

    // Initialize levers by data in sessionStorage
    const filters = JSON.parse(sessionStorage.filters);
    $favoritesOnly.prop('checked', filters.favoritesOnly);
    $categoryFilter.each(function () {
        const $this = $(this);
        const category = $this.data('category');
        $this.prop('checked', filters.categoriesWhiteList.includes(category));
    });

    $favoritesOnly.change(function () {
       const filters = JSON.parse(sessionStorage.filters);
       filters.favoritesOnly = this.checked;
       sessionStorage.filters = JSON.stringify(filters);
       updateVendors();
    });

    $categoryFilter.change(function () {
       const category = $(this).data('category');
       const filters = JSON.parse(sessionStorage.filters);
       if (this.checked)
           filters.categoriesWhiteList.push(category);
       else
           filters.categoriesWhiteList =
               filters.categoriesWhiteList.filter(x => x !== category);
       sessionStorage.filters = JSON.stringify(filters);
       updateVendors();
    });
});