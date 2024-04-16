// addon.js

$(document).ready(function () {
	"addon strict";
	$(".select-all").click(function () {
		var isChecked = $(this).prop("checked");
		$(".id-checkbox").prop("checked", isChecked);
	});
	$('.delete-selected').click(function () {
		var selectedIds = [];
		$('.id-checkbox:checked').each(function () {
			selectedIds.push($(this).val());
		});

		if (selectedIds.length > 0) {
			$.ajax({
				type: "DELETE",
				url: "/admin/addon/delete",
				contentType: 'application/json',
				data: JSON.stringify({ ids: selectedIds }),
				dataType: 'json',
				success: function (response) {
					for (var i = 0; i < selectedIds.length; i++) {
						const addonElement = document.getElementById('addon-' + selectedIds[i]);
						if (addonElement) {
							addonElement.remove();
						}
					}

					toastr.success(_('Delete Successfully'))
				},
				error: function (xhr, status, error) {
					toastr.error(_('Delete Faile'), xhr.responseText);
				}
			});
		} else {
			toastr.warning(_('Please first select the items you want to delete'));

		}
	});

	$(".switch-enable").click(function () {
		var isChecked = $(this).prop("checked");
		var plugin_name = $(this).data('uuid');
		console.log(isChecked)
		var formData = new FormData();
		formData.append('status', isChecked ? 'enabled' : "disabled");
		formData.append('plugin_name', plugin_name);

		$.ajax({
			type: "post",
			url: "/admin/addon/update/status",
			data: formData,
			contentType: false,
			processData: false,
			success: function (data) {
				toastr.success(_('Submit Successfully'))
			},
			error: function (data) {
				var message = data.responseJSON.message;
				toastr.error(message);
			}
		});
	});




	$(".btn-install").click(function () {
		var addon_id = $(this).data('id');
		var formData = new FormData();
		formData.append('addon_id', addon_id);
		$.ajax({
			type: "post",
			url: "/admin/addon/install",
			data: formData,
			contentType: false,
			processData: false,
			success: function (data) {
				toastr.success(_('Submit Successfully'))
				window.location.reload(true); 
			},
			error: function (data) {
				var message = data.responseJSON.message;
				toastr.error(message);
			}
		});
	});


	$(".btn-uninstall").click(function () {
		var addon_id = $(this).data('id');
		var formData = new FormData();
		formData.append('addon_id', addon_id);
		$.ajax({
			type: "post",
			url: "/admin/addon/uninstall",
			data: formData,
			contentType: false,
			processData: false,
			success: function (data) {
				toastr.success(_('Submit Successfully'))
				window.location.reload(true); 
			},
			error: function (data) {
				var message = data.responseJSON.message;
				toastr.error(message);
			}
		});
	});

});

function AddonSave() {
	"addon strict";
	document.getElementById("addon_button").disabled = true;
	document.getElementById("addon_button").innerHTML = "{{_('Please wait')}}";
	var formData = new FormData();
	if ($("#id").val() != undefined && $("#id").val() != 0 && $("#id").val() != "") {
		formData.append('id', $("#id").val());
	}
	formData.append('title', $("#title").val());
	formData.append('version', $("#version").val());
	formData.append('md5_hash', $("#md5_hash").val());
	formData.append('is_paid', $("#is_paid").val());
	formData.append('enabled', $("#enabled").val());

	$.ajax({
		type: "post",
		url: "/admin/addon/save",
		data: formData,
		contentType: false,
		processData: false,
		success: function (data) {
			toastr.success(_('Submit Successfully'))
			document.getElementById("addon_button").disabled = false;
			document.getElementById("addon_button").innerHTML = "Submit";
		},
		error: function (data) {
			var message = data.responseJSON.message;
			toastr.error(message);
			document.getElementById("addon_button").disabled = false;
			document.getElementById("addon_button").innerHTML = "Submit";
		}
	});
	return false;
}

function AddonDelete(AddonId) {
	if (confirm(_('Are you sure you want to delete it?'))) {
		var selectedIds = [AddonId];
		$.ajax({
			type: "DELETE",
			url: "/admin/addon/delete",
			contentType: 'application/json',
			data: JSON.stringify({ ids: selectedIds }),
			contentType: false,
			processData: false,
			success: function (data) {
				const addonElement = document.getElementById('addon-' + addonId);
				if (addonElement) {
					addonElement.remove();
				}
				toastr.success(localize.delete_done)
			},
			error: function (data) {
				var message = data.responseJSON.message;
				toastr.error(localize.delete_fail);
			}
		});
	}
	return false;
}

