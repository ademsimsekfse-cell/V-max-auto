// Plate auto-lookup
function lookupPlate(plate) {
    plate = plate.toUpperCase().replace(/\s/g, '');
    if (plate.length < 5) return;
    fetch(`/api/vehicles/search?plate=${encodeURIComponent(plate)}`)
        .then(r => r.json())
        .then(data => {
            if (data.found) {
                if (document.getElementById('brand')) document.getElementById('brand').value = data.brand || '';
                if (document.getElementById('model')) document.getElementById('model').value = data.model || '';
                if (document.getElementById('year')) document.getElementById('year').value = data.year || '';
                if (document.getElementById('color')) document.getElementById('color').value = data.color || '';
                if (document.getElementById('owner_name')) document.getElementById('owner_name').value = data.owner_name || '';
                if (document.getElementById('owner_phone')) document.getElementById('owner_phone').value = data.owner_phone || '';
                if (document.getElementById('vehicle_id')) document.getElementById('vehicle_id').value = data.id || '';
                const infoBox = document.getElementById('vehicle-info-box');
                if (infoBox) {
                    infoBox.innerHTML = `<div class="alert alert-success py-2"><i class="bi bi-check-circle me-1"></i><strong>${data.brand} ${data.model} ${data.year}</strong> — Sahip: ${data.owner_name || 'Kayıtsız'}</div>`;
                    infoBox.style.display = 'block';
                }
            } else {
                const infoBox = document.getElementById('vehicle-info-box');
                if (infoBox) {
                    infoBox.innerHTML = '<div class="alert alert-warning py-2"><i class="bi bi-exclamation-triangle me-1"></i>Bu plaka sistemde kayıtlı değil. Yeni araç olarak kaydedilecek.</div>';
                    infoBox.style.display = 'block';
                }
                // Clear vehicle fields
                ['brand','model','year','color','owner_name','owner_phone','vehicle_id'].forEach(id => {
                    const el = document.getElementById(id);
                    if (el) el.value = '';
                });
            }
        })
        .catch(err => console.error('Plate lookup error:', err));
}

// FAB toggle
document.addEventListener('DOMContentLoaded', function() {
    const fabMain = document.querySelector('.fab-main');
    const fabOptions = document.querySelector('.fab-options');
    if (fabMain && fabOptions) {
        fabMain.addEventListener('click', function(e) {
            e.stopPropagation();
            fabOptions.classList.toggle('show');
            this.style.transform = fabOptions.classList.contains('show') ? 'rotate(45deg)' : 'rotate(0deg)';
        });
        document.addEventListener('click', function(e) {
            if (!e.target.closest('.fab-container')) {
                fabOptions.classList.remove('show');
                if (fabMain) fabMain.style.transform = 'rotate(0deg)';
            }
        });
    }

    // Plate input listener
    const plateInput = document.getElementById('plate');
    if (plateInput) {
        let timer;
        plateInput.addEventListener('input', function() {
            clearTimeout(timer);
            timer = setTimeout(() => lookupPlate(this.value), 600);
        });
        plateInput.addEventListener('blur', function() {
            lookupPlate(this.value);
        });
    }

    // Quote/Invoice item total calculation
    document.querySelectorAll('.item-qty, .item-price').forEach(function(el) {
        el.addEventListener('input', calculateItemTotal);
    });
});

function calculateItemTotal() {
    const row = this.closest('tr');
    if (!row) return;
    const qty = parseFloat(row.querySelector('.item-qty')?.value) || 0;
    const price = parseFloat(row.querySelector('.item-price')?.value) || 0;
    const totalEl = row.querySelector('.item-total');
    if (totalEl) totalEl.value = (qty * price).toFixed(2);
    calculateGrandTotal();
}

function calculateGrandTotal() {
    let total = 0;
    document.querySelectorAll('.item-total').forEach(el => {
        total += parseFloat(el.value) || 0;
    });
    const taxRateEl = document.getElementById('tax_rate');
    const discountEl = document.getElementById('discount');
    const taxRate = taxRateEl ? (parseFloat(taxRateEl.value) || 18) : 18;
    const discount = discountEl ? (parseFloat(discountEl.value) || 0) : 0;
    const taxAmount = total * taxRate / 100;
    const finalAmount = total + taxAmount - discount;
    if (document.getElementById('total_amount')) document.getElementById('total_amount').value = total.toFixed(2);
    if (document.getElementById('tax_amount')) document.getElementById('tax_amount').value = taxAmount.toFixed(2);
    if (document.getElementById('final_amount')) document.getElementById('final_amount').value = finalAmount.toFixed(2);
}

function addItemRow(tableId) {
    const tbody = document.querySelector(`#${tableId} tbody`);
    if (!tbody) return;
    const tr = document.createElement('tr');
    tr.innerHTML = `
        <td><input type="text" class="form-control form-control-sm" name="item_description[]" required></td>
        <td>
            <select class="form-select form-select-sm" name="item_type[]">
                <option value="service">Hizmet</option>
                <option value="part">Parça</option>
            </select>
        </td>
        <td><input type="number" class="form-control form-control-sm item-qty" name="item_quantity[]" value="1" min="0.01" step="0.01"></td>
        <td><input type="number" class="form-control form-control-sm item-price" name="item_unit_price[]" value="0" min="0" step="0.01"></td>
        <td><input type="number" class="form-control form-control-sm item-total" name="item_total_price[]" value="0" readonly></td>
        <td><button type="button" class="btn btn-sm btn-danger" onclick="this.closest('tr').remove(); calculateGrandTotal()">×</button></td>
    `;
    tbody.appendChild(tr);
    tr.querySelectorAll('.item-qty, .item-price').forEach(el => {
        el.addEventListener('input', calculateItemTotal);
    });
}
