#!/usr/bin/env python

# Webserver for teletext editor with rest API

# Copyright 2015 Alistair Buxton <a.j.buxton@gmail.com>

# API:

# GET /<page>/<subpage>/
# Load subpage from disk at /data/<page>/<subpage>.tt and return
# it in url encoded fashion. Return a 404 if the subpage does not
# exist.

# POST /<page>/<subpage>/
# Receive a url encoded subpage in POST body and save it to disk
# at /data/<page>/<subpage>.tt. Creates any directories as required.

# GET /edit/<page>/<subpage>/
# Attempt to load subpage from disk at /data/<page>/<subpage>.tt
# If successful, serve a 303 redirect to:
#   /editor/<page>/<subpage>/#<urlendcodedpage>
# If unsuccessful, serve a 303 redirect to:
#   /editor/<page>/<subpage>/# (ie a blank subpage)

# GET /editor/<page>/<subpage>/
# Serve the teletext-editor.html

# Notes

# The editor does not have capability to POST pages, but this is
# the only feature which needs to be implemented for this whole
# thing to work. However, since this feature does not exist,
# I have not tested the code paths for POSTing subpages.

# Currently disk files are just a text file with the url encoded
# string. But by reimplementing storage2url and url2storage the
# pages can be stored in any format, including that used by
# pyteletext, which in combination with raspi-teletext would enable
# live editing of a service generated on raspberry pi.

# HEAD requests are not implemented.

from BaseHTTPServer import BaseHTTPRequestHandler,HTTPServer

import os, errno

ADDR = "localhost"
PORT = 8000

class RequestHandler(BaseHTTPRequestHandler):
    editor = open('teletext-editor.html').read()

    def datapath(self, page, create=False):
        path = os.path.join('data', '%03x'%page)
        if create:
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno == errno.EEXIST and os.path.isdir(path):
                    pass
                else: raise
        return path

    def storage2url(self, page, subpage):
        # for now just read/write the string
        filename = os.path.join(self.datapath(page), '%04x.tt'%subpage)
        data = file(filename).read()
        print filename, data
        return data

    def url2storage(self, page, subpage, urlencoded):
        filename = os.path.join(self.datapath(page, create=True), '%04x.tt'%subpage)
        f = file(filename, 'w')
        f.write(urlencoded)
        f.close()

    def do_store_page(self, page, subpage):
        self.url2storage(page, subpage, self.rfile.read())
        self.send_response(200, "OK")
        self.end_headers()
        self.wfile.close()        

    def do_get_page(self, page, subpage):
        try:
            urlencoded = self.storage2url(page, subpage)
        except:
            self.send_response(404, "Not found")
            self.end_headers()
            self.wfile.close()
            return
        self.send_response(200, "OK")
        self.end_headers()
        self.wfile.write(urlencoded)
        self.wfile.close()

    def do_edit(self, page, subpage):
        try:
            urlencoded = self.storage2url(page, subpage)
        except:
            urlencoded = ''
        self.send_response(303, "OK")
        self.send_header('Location', '/editor/%03x/%04x/#' % (page, subpage) + urlencoded)
        self.end_headers()
        self.wfile.close()

    def do_GET(self):
        try:
            data = self.path.strip('/').split('/')
            if len(data) == 2:
                self.do_get_page(int(data[0], 16), int(data[1], 16))
            elif len(data) == 3:
                if data[0] == 'edit':
                    self.do_edit(int(data[1], 16), int(data[2], 16))
                elif data[0] == 'editor':
                    self.send_response(200, "OK")
                    self.end_headers()
                    self.wfile.write(RequestHandler.editor)
                    self.wfile.close()
                else:
                    raise "ERROR"
            else:
                raise "ERROR"
        except:
            self.send_response(500, "Error")
            self.end_headers()
            self.wfile.write("There has been an error\n")
            self.wfile.close()

    def do_POST(self):
        try:
            data = self.path.strip('/').split('/')
            if len(data) == 2:
                self.do_post_page(int(data[0], 16), int(data[1], 16))
            else:
                raise "ERROR"
        except:
            self.send_response(500, "Error")
            self.end_headers()
            self.wfile.write("There has been an error\n")
            self.wfile.close()


httpd = HTTPServer((ADDR, PORT), RequestHandler)
httpd.serve_forever()
