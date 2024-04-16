$(document).ready(function () {
	"demo strict";
	$(".select-all").click(function () {
		var isChecked = $(this).prop("checked");
		$(".id-checkbox").prop("checked", isChecked);
	});
	$('.delete-selected').click(function () {
		var selectedIds = [];
		$('.id-checkbox:checked').each(function () {
			selectedIds.push($(this).val());
		});
        if (confirm(_('Are you sure you want to delete it?'))) {
			if (selectedIds.length > 0) {
				$.ajax({
					type: "DELETE",
					url: "/admin/addon/demo/delete",
					contentType: 'application/json',
					data: JSON.stringify({ ids: selectedIds }),
					dataType: 'json',
					success: function (response) {
						for (var i = 0; i < selectedIds.length; i++) {
							const demoElement = document.getElementById('demo-' + selectedIds[i]);
							if (demoElement) {
								demoElement.remove();
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
		}
	});

	$('.btn-submit').click(function (event) {
		event.preventDefault();
		var $this = $(this);
		$this.prop("disabled", true).html("{{_('Please wait')}}");
		$("#app-loading-indicator").removeClass("opacity-0");
		var formData = $('#demo_form').serialize();
		var type = $this.data('type');
		var buttonText = $this.text();
 
		$.ajax({
			type: "POST",
			url: "/admin/addon/demo/save",
			data: formData,
			contentType: 'application/x-www-form-urlencoded',
			processData: false,
			success: function (data) {
				toastr.success(_('Submit Successfully'));
				$this.prop("disabled", false).html(buttonText);
				if (type == 'submit-return') {
					window.location.href = '/admin/addon/demo';
				} else if (type == 'submit-new-entry') {
					window.location.href = '/admin/addon/demo/add';
				} else {
					window.location.reload();
				}
			},
			error: function (xhr, status, error) {
				let message = xhr.responseJSON.message;
				toastr.error(message);
				currentButton.prop("disabled", false);
			},
			complete: function (xhr, textStatus) {
				$("#app-loading-indicator").addClass("opacity-0");
			},
		});

		return false;
	});

	$('.btn-delete').click(function (event) {
		event.preventDefault();
		var $this = $(this);
		var TestId = $this.data('id');
		if (confirm(_('Are you sure you want to delete it?'))) {
			const selectedIds = [TestId];
			$("#app-loading-indicator").removeClass("opacity-0");
			$.ajax({
				type: "DELETE",
				url: "/admin/addon/demo/delete",
				contentType: 'application/json',
				data: JSON.stringify({ ids: selectedIds }),
				processData: false,
				success: function (data) {
					const demoElement = $('#demo-' + TestId);
					if (demoElement.length) {
						demoElement.remove();
					}
					toastr.success(localize.delete_done);
				},
				error: function (xhr, status, error) {
					let message = xhr.responseJSON.message;
					toastr.error(localize.delete_fail);
				},
				complete: function (xhr, textStatus) {
					$("#app-loading-indicator").addClass("opacity-0");
				},
			});
		}
		return false;
	})
});