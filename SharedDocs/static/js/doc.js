var waiting_response = false;
var t = null;

function clear_sync()
{
	// Keydown
	// Reset on every keydown
	clearTimeout(t);
	t = null;
}

function prepare_sync()
{
	// Keyup
	// Prepare synchronization
	if(t == null)
		t = setTimeout(function(){sync_doc()}, 500);
}

function sync_doc()
{
	if(waiting_response)
		return;
	var doc_uid = $('#raw_text').attr('doc_uid');
	$.post(
		'/docs/sync/' + doc_uid,
		{
			'doc': $('#raw_text').val(),
		},
		function(data){
			waiting_response = false;
			if(data.status_code != 0)
				return;
   	 		$('#raw_text').val(data.data);
		}
	);
	waiting_response = true;
}

function preview()
{
	var text = $('#raw_text').val();
	var converter = new showdown.Converter(),
   	html = converter.makeHtml(text);
   	$('#preview_text').html(html);
}

$(document).ready(function(){
	sync_doc();
	// Every now and then, sync with server, even no modifications.
	setInterval(function(){sync_doc()}, 1000);
});