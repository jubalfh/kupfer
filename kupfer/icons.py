from os import path

icon_cache = {}

# Fix bad icon names
# for example, gio returns "inode-directory" for folders
icon_name_translation = {
		"inode-directory": "folder",
		}

def get_icon(key):
	"""
	try retrieve icon in cache
	is a generator so it can be concisely called with a for loop
	"""
	if key not in icon_cache:
		return
	rec = icon_cache[key]
	rec["accesses"] += 1
	yield rec["icon"]

def store_icon(key, icon):
	if key in icon_cache:
		raise Exception("already in cache")
	icon_rec = {"icon":icon, "accesses":0}
	icon_cache[key] = icon_rec

def get_icon_for_gicon(gicon, icon_size):
	# FIXME: We can't load any general GIcon
	from gio import File, FILE_ATTRIBUTE_STANDARD_ICON, ThemedIcon, FileIcon
	if isinstance(gicon, FileIcon):
		ifile = gicon.get_file()
		return get_icon_from_file(ifile.get_path(), icon_size)
	if isinstance(gicon, ThemedIcon):
		names = gicon.get_names()
		return get_icon_for_name(names[0], icon_size, names)
	print "get_icon_for_gicon, could not load", gicon
	return None

def get_icon_for_file(uri, icon_size):
	"""
	Return a pixbuf representing the file at
	the @uri, which can be *either* and uri or a path

	return None if not found
	
	@icon_size: a pixel size of the icon
	"""
	from gtk import icon_theme_get_default
	from gio import File, FILE_ATTRIBUTE_STANDARD_ICON, ThemedIcon, FileIcon

	icon_theme = icon_theme_get_default()
	gfile = File(uri)
	if not gfile.query_exists():
		return None

	finfo = gfile.query_info(FILE_ATTRIBUTE_STANDARD_ICON)
	gicon = finfo.get_attribute_object(FILE_ATTRIBUTE_STANDARD_ICON)
	return get_icon_for_gicon(gicon, icon_size)

def get_icon_for_name(icon_name, icon_size, icon_names=[]):
	for i in get_icon(icon_name):
		return i
	from gtk import icon_theme_get_default, ICON_LOOKUP_USE_BUILTIN, ICON_LOOKUP_FORCE_SIZE
	from gobject import GError
	icon_theme = icon_theme_get_default()
	if not icon_names: icon_names = (icon_name,)

	# Try the whole list of given names
	for load_name in icon_names:
		# Possibly use a different name for lookup
		if load_name in icon_name_translation:
			load_name = icon_name_translation[load_name]
		try:
			icon = icon_theme.load_icon(load_name, icon_size, ICON_LOOKUP_USE_BUILTIN | ICON_LOOKUP_FORCE_SIZE)
			if icon:
				break
		except GError, e:
			icon = None
		except Exception, e:
			print "get_icon_for_name, error:", e
			icon = None
	else:
		# if we did not reach 'break' in the loop
		return None
	# We store the first icon in the list, even if the match
	# found was later in the chain
	store_icon(icon_name, icon)
	return icon

def get_icon_from_file(icon_file, icon_size):
	# try to load from cache
	for icon in get_icon(icon_file):
		return icon

	from gtk.gdk import pixbuf_new_from_file_at_size
	from gobject import GError
	try:
		icon = pixbuf_new_from_file_at_size(icon_file, icon_size, icon_size)
		store_icon(icon_file, icon)
		return icon
	except GError, e:
		print "get_icon_from_file, error:", e
		return None

def get_default_application_icon(icon_size):
	icon = get_icon_for_name("exec", icon_size)
	return icon
