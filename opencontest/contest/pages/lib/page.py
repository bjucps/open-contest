from datetime import datetime
import time
from uuid import uuid4

from contest.models.contest import Contest
from contest.pages.lib.htmllib import UIElement, div, h1, a, h2, h, head, body


def uuid():
    return str(uuid4())


class Header(UIElement):
    def __init__(self, title, endtimestamp=None):
        timeRemaining = ""
        if endtimestamp:
            timeRemaining = str(int(((endtimestamp / 1000) - time.time())))
        self.html = div(cls="top", contents=[
            div(cls="header", contents=[
                h1(title),
                div(cls="spacer"),
                div(cls="header-right", contents=[
                    h.span(cls="time-remaining", data_timeremaining=timeRemaining),
                    h.br(),
                    h.span(cls="login-user")
                ])
            ])
        ])


class MenuItem(UIElement):
    def __init__(self, url, title, role="any"):
        self.html = div(role=role, cls="menu-item", contents=[
            a(href=url, contents=[
                title
            ])
        ])


class Menu(UIElement):
    def __init__(self):
        self.html = div(cls="menu", contents=[
            div(cls="menu-items", contents=[
                MenuItem("/problems", "Problems"),
                MenuItem("/leaderboard", "Leaderboard"),
                MenuItem("/submissions", "My Submissions", role="participant"),
                MenuItem("/messages/inbox", "Messages"),
                MenuItem("/judge", "Judge", role="admin"),
                MenuItem("/setup", "Setup", role="admin"),
                MenuItem("/logout", "Logout")
            ])
        ])


class Footer(UIElement):
    def __init__(self):
        self.html = div(cls="footer", contents=[
            h2('Copyright &copy; {} by <a href="https://nathantheinventor.com" target="_blank">Nathan Collins</a> and BJU'.format(datetime.now().year)),
            div(cls="footer-links", contents=[
                h.span(h.a("System Status", href="/status")),
                h.span(h.a("Privacy Policy", href="/privacy", target="_blank")),
                h.span(h.a("About", href="/about", target="_blank")),
                h.span(h.a("FAQs", href="/faqs", target="_blank"))
            ])
        ])


class Page(UIElement):
    def __init__(self, *bodyData, cls='main-content'):
        cont = Contest.getCurrent()
        title = cont.name if cont else "OpenContest"
        self.html = h.html(
            head(
                h.title(title),
                h.link(rel="stylesheet", href="/static/lib/fontawesome/css/all.css", type="text/css"),
                h.link(rel="stylesheet", href="/static/lib/bootstrap/css/bootstrap.min.css", type="text/css"),
                h.link(rel="stylesheet", href="/static/lib/jqueryui/jquery-ui.min.css", type="text/css"),
                h.link(rel="stylesheet", href="/static/lib/simplemde/simplemde.min.css", type="text/css"),
                h.link(rel="stylesheet", href="/static/styles/style.css?" + uuid(), type="text/css"),
                h.link(rel="shortcut icon", href="/static/favicon.ico"),
                h.script(src="/static/lib/jquery/jquery.min.js"),
                h.script(src="/static/lib/bootstrap/js/bootstrap.min.js"),
                h.script(src="/static/lib/jqueryui/jquery-ui.min.js"),
                h.script(src="/static/lib/ace/ace.js"),
                h.script(src="/static/lib/simplemde/simplemde.min.js"),
                h.script(src="/static/scripts/script.js?" + uuid()),
                h.script(src="/static/lib/tablefilter/tablefilter.js"),
                h.script(src="/static/lib/FileSaver.min.js"),
            ),
            body(
                Header(title, cont.end if cont else None),
                Menu(),
                div(cls="message-alerts"),
                div(*bodyData, cls=cls),
                Footer()
            )
        )


class Card(UIElement):
    def __init__(self, title, contents, link=None, cls=None, delete=None, reply=None, rejudge=None, edit=None):
        if cls == None:
            cls = "card"
        else:
            cls += " card"
        deleteLink = ""
        if delete:
            deleteLink = div(h.i("clear", cls="material-icons"), cls="delete-link", onclick=delete)
        elif reply:
            deleteLink = div(h.button("Reply", cls="btn btn-primary", onclick=reply), cls="delete-link")
        if rejudge:
            deleteLink = div(h.button("Rejudge All", cls="btn btn-primary", onclick=rejudge), cls="delete-link")

                # Add a pencil to the card if one is desired
        editLink = ""
        if edit:
            editLink = div(h.i("edit", cls="material-icons", onclick=edit), cls="delete-link")
        
        self.html = h.div(cls=cls, contents=[
            div(cls="card-header", contents=[
                h2(contents=[title], cls="card-title"),
                deleteLink,
                editLink
            ]),
            div(cls="card-contents", contents=contents)
        ])
        if link != None:
            self.html = div(a(href=link, cls="card-link"), self.html, cls="card-link-box")


class Modal(UIElement):
    def __init__(self, title, body, footer, modalID=""):
        '''
        modalID - used to uniquely identify different modals. Only necessary when
                  two or more modals are present on page
        '''
        # taken from https://getbootstrap.com/docs/4.1/components/modal/
        self.html = div(cls=f"modal {modalID}", role="dialog", contents=[
            div(cls="modal-dialog", role="document", contents=[
                div(cls="modal-content", contents=[
                    div(cls="modal-header", contents=[
                        h.h5(title, cls="modal-title"),
                        h.button(**{"type": "button", "class": "close", "data-dismiss": "modal", "arial-label": "close"}, contents=[
                            h.span("&times;", **{"aria-hidden": "true"})
                        ])
                    ]),
                    div(body, cls="modal-body"),
                    div(footer, cls="modal-footer")
                ])
            ])
        ])
