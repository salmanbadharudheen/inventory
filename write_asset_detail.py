template_content = r"""{% extends 'base.html' %}

{% block page_title %}{{ asset.asset_tag }} - {{ asset.name }}{% endblock %}

{% block content %}
<div class="asset-detail-container" style="max-width: 1200px; margin: 0 auto; padding-bottom: 4rem;">
    <!-- Top Header Card -->
    <div class="card" style="margin-bottom: 2rem; border-radius: 16px; padding: 1.5rem 2rem;">
        <div style="display: flex; justify-content: space-between; align-items: start; flex-wrap: wrap; gap: 1.5rem;">
            <div style="display: flex; gap: 1.5rem; align-items: center;">
                {% if asset.image %}
                <div class="asset-image-preview" style="width: 80px; height: 80px; border-radius: 12px; overflow: hidden; border: 1px solid var(--border-color); background: #f8fafc;">
                    <img src="{{ asset.image.url }}" alt="{{ asset.name }}" style="width: 100%; height: 100%; object-fit: cover;">
                </div>
                {% else %}
                <div class="asset-image-placeholder" style="width: 80px; height: 80px; border-radius: 12px; background: #f1f5f9; display: flex; align-items: center; justify-content: center; color: #94a3b8;">
                    <i data-lucide="package" style="width: 32px; height: 32px;"></i>
                </div>
                {% endif %}
                <div>
                    <h1 style="margin: 0; font-size: 1.75rem; color: var(--text-primary);">{{ asset.name }}</h1>
                    <div style="display: flex; gap: 1rem; color: var(--text-secondary); margin-top: 0.5rem; font-size: 0.95rem;">
                        <span style="display: flex; align-items: center; gap: 0.4rem;"><i data-lucide="tag" style="width: 16px;"></i> {{ asset.asset_tag }}</span>
                        {% if asset.erp_asset_number %}
                        <span style="display: flex; align-items: center; gap: 0.4rem;"><i data-lucide="hash" style="width: 16px;"></i> ERP: {{ asset.erp_asset_number }}</span>
                        {% endif %}
                        <span style="display: flex; align-items: center; gap: 0.4rem;"><i data-lucide="layers" style="width: 16px;"></i> {{ asset.category.name }}</span>
                    </div>
                </div>
            </div>
            <div style="display: flex; gap: 0.75rem; align-items: center;">
                <span class="badge status-{{ asset.status|lower }}" style="font-size: 0.9rem; padding: 0.5rem 1.25rem; border-radius: 9999px; font-weight: 600;">{{ asset.get_status_display }}</span>
                <a href="{% url 'asset-update' asset.pk %}" class="btn btn-primary" style="display: flex; align-items: center; gap: 0.5rem;">
                    <i data-lucide="edit-2" style="width: 18px;"></i> Edit Asset
                </a>
            </div>
        </div>
    </div>

    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem;">
        <!-- Left Side: Main Details -->
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- 1. General Identification -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="info"></i><h3>General Identification</h3></div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Asset Name</span><span class="detail-value">{{ asset.name }}</span></div>
                    <div class="detail-item"><span class="detail-label">Asset ID (System)</span><span class="detail-value">{{ asset.asset_tag }}</span></div>
                    <div class="detail-item"><span class="detail-label">Asset Tag (Manual)</span><span class="detail-value">{{ asset.custom_asset_tag|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Asset Code</span><span class="detail-value">{{ asset.asset_code|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">ERP Asset Number</span><span class="detail-value">{{ asset.erp_asset_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Serial Number</span><span class="detail-value">{{ asset.serial_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Quantity</span><span class="detail-value">{{ asset.quantity }}</span></div>
                    <div class="detail-item"><span class="detail-label">Label Type</span><span class="detail-value">{{ asset.get_label_type_display }}</span></div>
                </div>
                {% if asset.description or asset.short_description %}
                <div style="margin-top: 1.25rem; padding-top: 1.25rem; border-top: 1px solid var(--border-color);">
                    {% if asset.short_description %}
                    <div style="margin-bottom: 0.75rem;">
                        <span class="detail-label">Short Description</span>
                        <p style="margin: 0.25rem 0 0; font-size: 0.95rem;">{{ asset.short_description }}</p>
                    </div>
                    {% endif %}
                    {% if asset.description %}
                    <div>
                        <span class="detail-label">Full Description</span>
                        <p style="margin: 0.25rem 0 0; font-size: 0.95rem; line-height: 1.5;">{{ asset.description }}</p>
                    </div>
                    {% endif %}
                </div>
                {% endif %}
            </div>

            <!-- 2. Categorization -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="grid"></i><h3>Categorization</h3></div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Category</span><span class="detail-value">{{ asset.category.name }}</span></div>
                    <div class="detail-item"><span class="detail-label">Sub Category</span><span class="detail-value">{{ asset.sub_category.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Group</span><span class="detail-value">{{ asset.group.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Sub Group</span><span class="detail-value">{{ asset.sub_group.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Asset Type</span><span class="detail-value">{{ asset.get_asset_type_display }}</span></div>
                    <div class="detail-item"><span class="detail-label">Brand</span><span class="detail-value">{% if asset.brand_new %}{{ asset.brand_new.name }}{% elif asset.brand %}{{ asset.brand }}{% else %}-{% endif %}</span></div>
                    <div class="detail-item"><span class="detail-label">Model</span><span class="detail-value">{{ asset.model|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Condition</span><span class="detail-value">{{ asset.get_condition_display }}</span></div>
                </div>
            </div>

            <!-- 3. Location Details -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="map-pin"></i><h3>Location Hierarchy</h3></div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Region</span><span class="detail-value">{{ asset.region.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Branch/Entity</span><span class="detail-value">{{ asset.branch.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Site</span><span class="detail-value">{{ asset.site.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Building</span><span class="detail-value">{{ asset.building.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Floor</span><span class="detail-value">{{ asset.floor.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Location</span><span class="detail-value">{{ asset.location.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Sub-Location</span><span class="detail-value">{{ asset.sub_location.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Room / Precise Area</span><span class="detail-value">{{ asset.room.name|default:"-" }}</span></div>
                </div>
            </div>

            <!-- 4. Ownership & Assignment -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="user"></i><h3>Ownership & Assignment</h3></div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Company Owned By</span><span class="detail-value">{{ asset.company.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Department</span><span class="detail-value">{{ asset.department.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Cost Center</span><span class="detail-value">{{ asset.cost_center|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Assigned User</span><span class="detail-value">{% if asset.assigned_to %}{{ asset.assigned_to.get_full_name|default:asset.assigned_to.username }}{% else %}Unassigned{% endif %}</span></div>
                    <div class="detail-item"><span class="detail-label">Employee Number</span><span class="detail-value">{{ asset.employee_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Custodian</span><span class="detail-value">{{ asset.custodian.name|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Supplier</span><span class="detail-value">{{ asset.supplier.name|default:"-" }}</span></div>
                </div>
            </div>

            <!-- 5. Financial & Procurement -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="dollar-sign"></i><h3>Financial & Procurement</h3></div>
                <div class="financial-summary" style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; padding: 1rem; background: #f8fafc; border-radius: 12px; margin-bottom: 1.5rem;">
                    <div style="text-align: center;"><span class="detail-label">Purchase Price</span><div style="font-size: 1.25rem; font-weight: 700; color: var(--text-primary);">{{ asset.currency }} {{ asset.purchase_price|default:"0.00" }}</div></div>
                    <div style="text-align: center;"><span class="detail-label">Current Value</span><div style="font-size: 1.25rem; font-weight: 700; color: var(--primary);">{{ asset.currency }} {{ asset.current_value|default:"0.00" }}</div></div>
                    <div style="text-align: center;"><span class="detail-label">Accumulated Depr.</span><div style="font-size: 1.25rem; font-weight: 700; color: #ef4444;">{{ asset.currency }} {{ asset.accumulated_depreciation|default:"0.00" }}</div></div>
                </div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Purchase Date</span><span class="detail-value">{{ asset.purchase_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Invoice Number</span><span class="detail-value">{{ asset.invoice_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Invoice Date</span><span class="detail-value">{{ asset.invoice_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">PO Number</span><span class="detail-value">{{ asset.po_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">PO Date</span><span class="detail-value">{{ asset.po_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">DO Number</span><span class="detail-value">{{ asset.do_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">DO Date</span><span class="detail-value">{{ asset.do_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">GRN Number</span><span class="detail-value">{{ asset.grn_number|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Date in Service</span><span class="detail-value">{{ asset.date_placed_in_service|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Tagged Date</span><span class="detail-value">{{ asset.tagged_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Vendor</span><span class="detail-value">{{ asset.vendor.name|default:"-" }}</span></div>
                </div>
                <div style="margin-top: 1.5rem; padding-top: 1.5rem; border-top: 1px solid var(--border-color);">
                    <h4 style="margin-top: 0; font-size: 1rem; color: var(--text-primary);">Depreciation Policy</h4>
                    <div class="detail-grid" style="margin-top: 1rem;">
                        <div class="detail-item"><span class="detail-label">Method</span><span class="detail-value">{{ asset.get_depreciation_method_display }}</span></div>
                        <div class="detail-item"><span class="detail-label">Useful Life</span><span class="detail-value">{{ asset.useful_life_years }} Years</span></div>
                        <div class="detail-item"><span class="detail-label">Salvage Value</span><span class="detail-value">{{ asset.currency }} {{ asset.salvage_value|default:"0.00" }}</span></div>
                    </div>
                </div>
            </div>

            <!-- 6. Warranty & Maintenance -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="shield-check"></i><h3>Warranty, Maintenance & Insurance</h3></div>
                <div class="detail-grid">
                    <div class="detail-item"><span class="detail-label">Warranty Start</span><span class="detail-value">{{ asset.warranty_start|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Warranty End</span><span class="detail-value">{{ asset.warranty_end|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Maintenance Start</span><span class="detail-value">{{ asset.maintenance_start_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Maintenance End</span><span class="detail-value">{{ asset.maintenance_end_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Next Maintenance</span><span class="detail-value">{{ asset.next_maintenance_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Maint. Frequency</span><span class="detail-value">{% if asset.maintenance_required %}{{ asset.maintenance_frequency_days }} Days{% else %}Not Required{% endif %}</span></div>
                    <div class="detail-item"><span class="detail-label">Insurance Start</span><span class="detail-value">{{ asset.insurance_start_date|date:"d M Y"|default:"-" }}</span></div>
                    <div class="detail-item"><span class="detail-label">Insurance End</span><span class="detail-value">{{ asset.insurance_end_date|date:"d M Y"|default:"-" }}</span></div>
                </div>
            </div>
        </div>

        <!-- Right Side: QR, Files & Notes -->
        <div style="display: flex; flex-direction: column; gap: 1.5rem;">
            <!-- QR Code Card -->
            <div class="card" style="text-align: center; padding: 2rem;">
                <div id="qr-container" style="background: white; width: 180px; height: 180px; margin: 0 auto; padding: 10px; border: 1px solid var(--border-color); border-radius: 12px; display: flex; align-items: center; justify-content: center;">
                    <i data-lucide="qr-code" style="width: 120px; height: 120px; color: #1e293b; opacity: 0.1;"></i>
                </div>
                <div style="margin-top: 1.5rem;">
                    <div style="font-weight: 700; font-size: 1.1rem; color: var(--text-primary);">{{ asset.asset_tag }}</div>
                    <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 0.25rem;">Scan for asset details</div>
                </div>
                <button class="btn" style="margin-top: 1.5rem; width: 100%; border: 1px solid var(--border-color); background: white;"><i data-lucide="printer" style="width: 16px; margin-right: 0.5rem;"></i> Print Label</button>
            </div>

            <!-- Documents & Attachments -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="paperclip"></i><h3>Documents</h3></div>
                <div style="display: flex; flex-direction: column; gap: 0.75rem; margin-top: 1rem;">
                    {% if asset.po_file %}<a href="{{ asset.po_file.url }}" target="_blank" class="document-link"><i data-lucide="file-text"></i><span>Purchase Order</span></a>{% endif %}
                    {% if asset.invoice_file %}<a href="{{ asset.invoice_file.url }}" target="_blank" class="document-link"><i data-lucide="file-check"></i><span>Invoice / Contract</span></a>{% endif %}
                    {% if asset.delivery_note_file %}<a href="{{ asset.delivery_note_file.url }}" target="_blank" class="document-link"><i data-lucide="truck"></i><span>Delivery Note</span></a>{% endif %}
                    {% if asset.insurance_file %}<a href="{{ asset.insurance_file.url }}" target="_blank" class="document-link"><i data-lucide="shield"></i><span>Insurance Policy</span></a>{% endif %}
                    {% if asset.amc_file %}<a href="{{ asset.amc_file.url }}" target="_blank" class="document-link"><i data-lucide="clipboard-list"></i><span>AMC Document</span></a>{% endif %}
                    {% if not asset.po_file and not asset.invoice_file and not asset.delivery_note_file and not asset.insurance_file and not asset.amc_file %}
                    <div style="text-align: center; padding: 2rem 1rem; color: var(--text-secondary); font-size: 0.9rem;">
                        <i data-lucide="file-question" style="width: 32px; height: 32px; opacity: 0.2; margin-bottom: 0.5rem;"></i>
                        <p>No documents attached to this asset.</p>
                    </div>
                    {% endif %}
                </div>
                <button class="btn" style="width: 100%; margin-top: 1.25rem; background: #f8fafc; border: 1px dashed var(--border-color); color: var(--text-secondary); font-size: 0.85rem;">+ Manage Files</button>
            </div>

            <!-- Notes & Remarks -->
            <div class="card detail-section">
                <div class="section-header"><i data-lucide="message-square"></i><h3>Notes & Remarks</h3></div>
                {% if asset.asset_remarks %}
                <div style="margin-bottom: 1rem;"><span class="detail-label">Standard Remark</span><div style="font-weight: 600; color: var(--text-primary); margin-top: 0.25rem;">{{ asset.asset_remarks.remark }}</div></div>
                {% endif %}
                {% if asset.notes %}
                <div><span class="detail-label">General Notes</span><p style="margin: 0.5rem 0 0; font-size: 0.95rem; background: #fdfae6; padding: 1rem; border-radius: 8px; border-left: 4px solid #fbbf24;">{{ asset.notes }}</p></div>
                {% else %}<p style="color: var(--text-secondary); font-size: 0.9rem; margin-top: 1rem;">No custom notes added.</p>{% endif %}
            </div>
        </div>
    </div>
</div>

<style>
    .detail-section h3 { margin: 0; font-size: 1.15rem; font-weight: 700; color: var(--text-primary); }
    .section-header { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 1.5rem; color: var(--primary); }
    .section-header i { width: 20px; height: 20px; }
    .detail-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1.25rem; }
    .detail-item { display: flex; flex-direction: column; gap: 0.35rem; }
    .detail-label { font-size: 0.75rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.05em; color: var(--text-secondary); }
    .detail-value { font-size: 1rem; font-weight: 500; color: var(--text-primary); }
    .status-active { background: #dcfce7; color: #166534; }
    .status-in_storage { background: #dbeafe; color: #1e40af; }
    .status-under_maintenance { background: #fef3c7; color: #92400e; }
    .status-lost, .status-stolen { background: #fee2e2; color: #991b1b; }
    .status-retired { background: #f1f5f9; color: #475569; }
    .document-link { display: flex; align-items: center; gap: 0.75rem; padding: 0.85rem 1rem; background: white; border: 1px solid var(--border-color); border-radius: 10px; text-decoration: none; color: var(--text-primary); transition: all 0.2s; }
    .document-link:hover { border-color: var(--primary); background: #f0f7ff; color: var(--primary); transform: translateY(-1px); }
    .document-link i { width: 18px; color: var(--text-secondary); }
    .document-link:hover i { color: var(--primary); }
</style>
{% endblock %}
"""

with open('templates/assets/asset_detail.html', 'w', encoding='utf-8') as f:
    f.write(template_content)
