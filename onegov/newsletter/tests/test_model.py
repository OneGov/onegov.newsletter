import pytest
import transaction

from freezegun import freeze_time
from onegov.newsletter import Newsletter, Recipient
from onegov.newsletter.models import newsletter_recipients
from sqlalchemy.exc import IntegrityError


def test_newsletter_date(session):
    with freeze_time('2016-01-29 14:00'):
        newsletter = Newsletter(
            title="The weekly gossip",
            content="<h1>The weekly gossip"
        )
        session.add(newsletter)
        session.flush()

    assert newsletter.date.year == 2016
    assert newsletter.date.month == 1
    assert newsletter.date.day == 29
    assert newsletter.date.hour == 14


def test_recipients_unique_per_group(session):

    for group in (None, 'foo', 'bar'):
        session.add(Recipient(address='info@example.org', group=group))
        transaction.commit()

        with pytest.raises(IntegrityError):
            session.add(Recipient(address='info@example.org', group=group))
            session.flush()

        transaction.abort()


def test_newsletter_recipients_cascade(session):

    # is the relationship reflected correctly?
    newsletter = Newsletter(
        title="10 things you didn't know",
        content="<h1>10 things you didn't know</h1>",
        recipients=[
            Recipient(address='info@example.org')
        ]
    )

    session.add(newsletter)
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    recipient = session.query(Recipient).first()

    assert len(newsletter.recipients) == 1
    assert len(recipient.newsletters) == 1
    assert session.query(newsletter_recipients).count() == 1

    # is the delete cascaded if the newsletter is deleted?
    session.delete(newsletter)
    transaction.commit()

    recipient = session.query(Recipient).first()
    assert len(recipient.newsletters) == 0
    assert session.query(newsletter_recipients).count() == 0

    # is the delete cascaded if the recipient is deleted?
    recipient.newsletters.append(Newsletter(
        title="How Bitcoin is so 90s",
        content="<h1>How Bitcoin is so 90s</h1>"
    ))
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    session.delete(newsletter.recipients[0])
    transaction.commit()

    newsletter = session.query(Newsletter).first()
    assert len(newsletter.recipients) == 0
    assert session.query(newsletter_recipients).count() == 0