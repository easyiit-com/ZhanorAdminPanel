$(document).ready(function () {
	"use strict";
	var modelEditor, templateIndexEditor, templateAddEditor, templateEditEditor, viewsEditor, jsEditor, routeEditor;

	// 初始化编辑器的函数
	function initAceEditor(elementId, mode) {
		var editor = ace.edit(elementId);
		editor.session.setMode("ace/mode/" + mode);
		editor.setTheme("ace/theme/dracula");
		return editor;
	}

	modelEditor = initAceEditor("model_code", "python");
	templateIndexEditor = initAceEditor('template_index_code', 'html');
	templateAddEditor = initAceEditor('template_add_code', 'html');
	templateEditEditor = initAceEditor('template_edit_code', 'html');
	viewsEditor = initAceEditor('views_code', 'python');
	jsEditor = initAceEditor('js_code', 'javascript');
	routeEditor = initAceEditor('route_code', 'python');

	$("body").on("change", ".table_name", function () {
		const tableName = $(this).val();
		console.log(tableName);

		var formData = new FormData();
		formData.append('table_name', tableName);
		$.ajax({
			type: "post",
			url: "/admin/plugins/generator/code",
			data: formData,
			contentType: false,
			processData: false,
			success: function (data) {
				var list = data.data.table_fields;

				var checkboxesHtml = '';
				for (var i = 0; i < list.length; i++) {
					checkboxesHtml += '<label class="form-check form-check-inline"><input class="form-check-input table_fields" type="checkbox" type="checkbox" name="fields[]" value="' + list[i] + '" checked><span class="form-check-label">' + list[i] + '</span></label>';
				}

				show_code(data.data.model_code, data.data.template_index_code, data.data.template_add_code, data.data.template_edit_code, data.data.views_code, data.data.js_code, data.data.route_code)
				$('#table_fields').on('click', '.table_fields', function () {
					const tableName = $('#table_name').val();
					console.log(tableName);
					var checkedValues = $('.table_fields:checked').map(function () {
						return this.value;
					}).get().join(",");
					    var formData = new FormData();
						formData.append('table_name', tableName);
						formData.append('fields', checkedValues);
						$.ajax({
							type: "post",
							url: "/admin/plugins/generator/code",
							data: formData,
							contentType: false,
							processData: false,
							success: function (data) {
								show_code(data.data.model_code, data.data.template_index_code, data.data.template_add_code, data.data.template_edit_code, data.data.views_code, data.data.js_code, data.data.route_code)
								toastr.success('Get Successfully')
							}
						});
				});
				$('#table_fields').html(checkboxesHtml);

				toastr.success('Get Successfully')
			},
			error: function (data) {
				var err = data.responseJSON.errors;
				$.each(err, function (index, value) {
					toastr.error(value);
				});
				document.getElementById("generator_button").disabled = false;
				document.getElementById("generator_button").innerHTML = "Save";
			}
		});
	});

	function show_code(model_code, template_index_code, template_add_code, template_edit_code, views_code, js_code, route_code) {
		modelEditor.setValue(model_code);
		templateIndexEditor.setValue(template_index_code);
		templateAddEditor.setValue(template_add_code);
		templateEditEditor.setValue(template_edit_code);
		viewsEditor.setValue(views_code);
		jsEditor.setValue(js_code);
		routeEditor.setValue(route_code);
	};

	function fields_change() {
		$('.table_fields"]').on('click', function () {
			const tableName = $('#table_name').val();
			console.log(tableName);

			var checkedValues = $('.table_fields:checked').map(function () {
				return this.value;
			}).get().join(",");
			console.log(checkedValues);

			$.ajax({
				type: "get",
				url: "/admin/plugins/generator/code/" + tableName,
				success: function (data) {
					var list = data.data.table_fields;

					var checkboxesHtml = '';
					for (var i = 0; i < list.length; i++) {
						checkboxesHtml += '<label class="form-check form-check-inline"><input class="form-check-input" type="checkbox" type="checkbox" name="fields[]" value="' + list[i] + '" checked><span class="form-check-label">' + list[i] + '</span></label>';
					}

					$('#table_fields').html(checkboxesHtml);

					modelEditor.setValue(data.data.model_code);
					templateIndexEditor.setValue(data.data.template_index_code);
					templateAddEditor.setValue(data.data.template_add_code);
					templateEditEditor.setValue(data.data.template_edit_code);
					viewsEditor.setValue(data.data.views_code);
					jsEditor.setValue(data.data.js_code);
					routeEditor.setValue(data.data.route_code);
					toastr.success('Get Successfully')
				},
				error: function (data) {
					var err = data.responseJSON.errors;
					$.each(err, function (index, value) {
						toastr.error(value);
					});
					document.getElementById("generator_button").disabled = false;
					document.getElementById("generator_button").innerHTML = "Save";
				}
			});
		});
	}


	function generator() {
		"use strict";

		document.getElementById("generator_button").disabled = true;
		document.getElementById("generator_button").innerHTML = "{{_('Please wait')}}";

		var formData = new FormData();
		formData.append('table_name', $("#table_name").val());
		formData.append('model_code', modelEditor.getValue());
		formData.append('template_index_code', templateIndexEditor.getValue());
		formData.append('template_add_code', templateAddEditor.getValue());
		formData.append('template_edit_code', templateEditEditor.getValue());
		formData.append('views_code', viewsEditor.getValue());
		formData.append('js_code', jsEditor.getValue());
		formData.append('route_code', routeEditor.getValue());

		$.ajax({
			type: "post",
			url: "/admin/plugins/generator/generate",
			data: formData,
			contentType: false,
			processData: false,
			success: function (data) {
				toastr.success(_('Submit Successfully'))
				document.getElementById("generator_button").disabled = false;
				document.getElementById("generator_button").innerHTML = "Submit";
			},
			error: function (data) {
				var message = data.responseJSON.message;
				toastr.error(message);
				document.getElementById("generator_button").disabled = false;
				document.getElementById("generator_button").innerHTML = "Submit";
			}
		});
		return false;
	}

	// 绑定按钮点击事件
	$("#generator_button").click(function (event) {
		event.preventDefault(); // 阻止按钮的默认行为（如表单提交）
		// 调用 generator 函数
		generator();
	});
});
