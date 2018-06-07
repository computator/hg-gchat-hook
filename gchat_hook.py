from mercurial import cmdutil
try:
	from mercurial import color
except ImportError:
	pass
import urllib2
import json

def push_notify(ui, repo, node, node_last, url, **kwargs):
	notify_url = ui.config('gchat', 'notify_url')
	if not notify_url:
		ui.warn("Skipping push_notify hook because notify_url is not set for gchat\n")
		return True
	tpl = ui.config('gchat', 'notify_template', "{count} changesets {action} from repository _{url}_:\n\n{log}\n")
	log_tpl = ui.config('gchat', 'notify_log_template', 'status')

	try:
		orig_color = ui.config('ui', 'color')
		ui.setconfig('ui', 'color', 'off')
		color.setup(ui)
	except ImportError:
		pass

	revs = repo.revs('{}:{}'.format(node_last, node))
	disp = cmdutil.show_changeset(ui, repo, {'template': log_tpl})
	logtext = ''
	for rev in revs:
		ui.pushbuffer(labeled=False)
		disp.show(repo[rev])
		newtext = ui.popbuffer()
		if len(logtext) + len(newtext) + len(tpl) > 4000:
			logtext += "\n*Changeset log truncated...*"
			break
		logtext += newtext
	disp.close()

	try:
		ui.setconfig('ui', 'color', orig_color)
		color.setup(ui)
	except ImportError:
		pass

	args = {
		'count': len(revs),
		'action': 'pushed' if kwargs['source'] == 'serve' else kwargs['source'].rstrip('e') + 'ed',
		'source': kwargs['source'],
		'url': url,
		'log': logtext
	}
	text = tpl.format(**args)
	if len(text) > 4096:
		text = text[:4096-16] + "_<truncated...>_"

	req = urllib2.Request(notify_url, json.dumps({'text': text}), {'Content-Type': 'application/json'})
	urllib2.urlopen(req, timeout=10)
