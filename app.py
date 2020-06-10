# ----------------------------------------------------------------------------#
# Imports
# ----------------------------------------------------------------------------#
import sys
import json
import dateutil.parser
import babel
from flask import (
    Flask,
    render_template,
    request,
    Response,
    flash,
    redirect,
    url_for)
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate

from config import SQLALCHEMY_DATABASE_URI

# ----------------------------------------------------------------------------#
# App Config.
# ----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

migrate = Migrate(app, db)
current_time = datetime.now()


# ----------------------------------------------------------------------------#
# Models.
# ----------------------------------------------------------------------------#


class Venue(db.Model):
    __tablename__ = 'venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    seeking_talent = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(500), default=None)
    shows = db.relationship('Show', backref='venue', lazy=True)

    def __init__(self, name, city, state, address, phone, genres, image_link=None, facebook_link=None, website=None,
                 seeking_talent=False, seeking_description=None):
        self.name = name
        self.city = city
        self.state = state
        self.address = address
        self.phone = phone
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.website = website
        self.genres = genres
        self.seeking_talent = seeking_talent
        self.seeking_description = seeking_description

    def venue_data(self):
        return {
            "id": self.id,
            "name": self.name,
            "num_upcoming_shows": len([show.id for show in self.shows if show.start_time > current_time]),
        }

    def __repr__(self):
        return f'<class {self.__class__.__name__} {self.id} {self.name}>'


class Artist(db.Model):
    __tablename__ = 'artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    city = db.Column(db.String(120), nullable=False)
    state = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(120))
    genres = db.Column(db.ARRAY(db.String(120)))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    seeking_venue = db.Column(db.Boolean, nullable=False, default=False)
    seeking_description = db.Column(db.String(1000), default=None)
    shows = db.relationship('Show', backref='artist', lazy=True)

    def __init__(self, name, city, state, phone, genres, image_link=None, facebook_link=None, website=None,
                 seeking_venue=False, seeking_description=None):
        self.name = name
        self.city = city
        self.state = state
        self.phone = phone
        self.genres = genres
        self.image_link = image_link
        self.facebook_link = facebook_link
        self.website = website
        self.seeking_venue = seeking_venue
        self.seeking_description = seeking_description

    def __repr__(self):
        return f'<class {self.__class__.__name__} {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    venue_id = db.Column(db.Integer, db.ForeignKey('venue.id'), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'), nullable=False)
    start_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, venue_id, artist_id, start_time):
        self.venue_id = venue_id
        self.artist_id = artist_id
        self.start_time = start_time

    def artist_details(self):
        return {
            'artist_id': self.venue_id,
            'artist_name': self.artist.name,
            'artist_image_link': self.artist.image_link,
            'start_time': str(self.start_time)
        }

    def venue_details(self):
        return {
            'venue_id': self.venue_id,
            'venue_name': self.venue.name,
            'venue_image_link': self.venue.image_link,
            'start_time': str(self.start_time)
        }

    def show_details(self):
        return {
            "venue_id": self.venue_id,
            "venue_name": self.venue.name,
            "artist_id": self.artist_id,
            "artist_name": self.artist.name,
            "artist_image_link": self.artist.image_link,
            "start_time": str(self.start_time)
        }

    def __repr__(self):
        return f'<class {self.__class__.__name__} {self.id}>'


# ----------------------------------------------------------------------------#
# Filters.
# ----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format)


app.jinja_env.filters['datetime'] = format_datetime


# ----------------------------------------------------------------------------#
# Controllers.
# ----------------------------------------------------------------------------#

@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
    venues = Venue.query.group_by(Venue.id, Venue.state, Venue.city).all()
    venue_state_and_city = ""
    data = []

    # loop through venues to check for upcoming shows, city, states and venue information
    for venue in venues:
        if venue_state_and_city == venue.city + venue.state:
            data[len(data) - 1]["venues"].append(venue.venue_data())
        else:
            venue_state_and_city = venue.city + venue.state
            data.append({
                "city": venue.city,
                "state": venue.state,
                "venues": [venue.venue_data()]
            })
    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    # Below is the search query which returns list of all matched venues
    venues_list = Venue.query.filter(Venue.name.ilike('%' + search_term + '%')).all()
    response = {
        "count": len(venues_list),
        "data": [venue.venue_data() for venue in venues_list]
    }
    return render_template('pages/search_venues.html', results=response, search_term=search_term)


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    venue = Venue.query.get(venue_id)
    upcoming_shows = [show.artist_details() for show in venue.shows if show.start_time >= current_time]
    past_shows = [show.artist_details() for show in venue.shows if show.start_time < current_time]
    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres,
        "address": venue.address,
        "city": venue.city,
        "state": venue.state,
        "phone": venue.phone,
        "website": venue.website,
        "facebook_link": venue.facebook_link,
        "seeking_talent": venue.seeking_talent,
        "seeking_description": venue.seeking_description,
        "image_link": venue.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_venue.html', venue=data)


#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        form_data = request.form
        seeking_talent_data = True if form_data.get("seeking_talent") == "True" else False
        if not seeking_talent_data:
            seeking_description_data = None
        else:
            seeking_description_data = form_data.get("seeking_description")
        new_venue = Venue(
            name=form_data.get("name"),
            city=form_data.get("city"),
            state=form_data.get("state"),
            address=form_data.get("address"),
            phone=form_data.get("phone"),
            genres=form_data.getlist("genres"),
            facebook_link=form_data.get("facebook_link"),
            image_link=form_data.get("image_link"),
            website=form_data.get("website"),
            seeking_talent=seeking_talent_data,
            seeking_description=seeking_description_data
        )
        db.session.add(new_venue)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Venue ' + form_data.get("name") + ' could not be listed.')
    else:
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
        return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # TODO: Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
    try:
        venue = Venue.query.get(venue_id)
        venue_name = venue.name
        db.session.delete(venue)
        db.session.commit()
        flash('Venue ' + venue_name + ' was successfully deleted!')
    except:
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
    data = [{"id": artist.id, "name": artist.name} for artist in Artist.query.all()]
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    req_artist_list = Artist.query.filter(Artist.name.ilike("%" + search_term + "%")).all()
    # Note: There is no point in giving "num_upcoming_shows" data in response. so, didn't add that data in response
    response = {
        "count": len(req_artist_list),
        "data": [{"id": artist.id, "name": artist.name} for artist in req_artist_list]
    }
    return render_template('pages/search_artists.html', results=response, search_term=search_term)


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    artist = Artist.query.get(artist_id)
    upcoming_shows = [show.venue_details() for show in artist.shows if show.start_time >= current_time]
    past_shows = [show.venue_details() for show in artist.shows if show.start_time < current_time]

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": artist.genres,
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "seeking_venue": artist.seeking_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past_shows),
        "upcoming_shows_count": len(upcoming_shows),
    }
    return render_template('pages/show_artist.html', artist=data)


#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    artist_data = Artist.query.get(artist_id)
    artist = {
        "id": artist_data.id,
        "name": artist_data.name,
        "genres": artist_data.genres,
        "city": artist_data.city,
        "state": artist_data.state,
        "phone": artist_data.phone,
        "website": artist_data.website,
        "facebook_link": artist_data.facebook_link,
        "seeking_venue": artist_data.seeking_venue,
        "seeking_description": artist_data.seeking_description,
        "image_link": artist_data.image_link
    }
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # TODO: take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    error = False
    try:
        data = request.form
        seeking_venue_data = True if data.get("seeking_venue") == "True" else False
        if not seeking_venue_data:
            seeking_description_data = None
        else:
            seeking_description_data = data.get("seeking_description")
        artist = Artist.query.get(artist_id)
        artist.name = data.get("name")
        artist.genres = data.getlist("genres")
        artist.city = data.get("city")
        artist.state = data.get("state")
        artist.phone = data.get("phone")
        artist.website = data.get("website")
        artist.facebook_link = data.get("facebook_link")
        artist.image_link = data.get("image_link")
        artist.seeking_venue = seeking_venue_data
        artist.seeking_description = seeking_description_data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred while updating ' + request.form['name'])
        return redirect(url_for('show_artist', artist_id=artist_id))
    else:
        flash('Artist ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue_data = Venue.query.get(venue_id)
    venue = {
        "id": venue_data.id,
        "name": venue_data.name,
        "genres": venue_data.genres,
        "address": venue_data.address,
        "city": venue_data.city,
        "state": venue_data.state,
        "phone": venue_data.phone,
        "website": venue_data.website,
        "facebook_link": venue_data.facebook_link,
        "seeking_talent": venue_data.seeking_talent,
        "seeking_description": venue_data.seeking_description,
        "image_link": venue_data.image_link
    }
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # TODO: take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    error = False
    try:
        venue = Venue.query.get(venue_id)
        form_data = request.form
        seeking_talent_data = True if form_data.get("seeking_talent") == "True" else False
        if not seeking_talent_data:
            seeking_description_data = None
        else:
            seeking_description_data = form_data.get("seeking_description")
        print("form_data", form_data)
        venue.name = form_data.get("name")
        venue.city = form_data.get("city")
        venue.state = form_data.get("state")
        venue.address = form_data.get("address")
        venue.phone = form_data.get("phone")
        venue.genres = form_data.getlist("genres")
        venue.facebook_link = form_data.get("facebook_link")
        venue.image_link = form_data.get("image_link")
        venue.website = form_data.get("website")
        venue.seeking_talent = seeking_talent_data
        venue.seeking_description = seeking_description_data
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred while updating ' + request.form['name'])
        return redirect(url_for('show_venue', venue_id=venue_id))
    else:
        flash('Venue ' + request.form['name'] + ' was successfully updated!')
        return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # TODO: insert form data as a new Venue record in the db, instead
    # TODO: modify data to be the data object returned from db insertion
    error = False
    try:
        form_data = request.form
        seeking_venue_data = True if form_data.get("seeking_venue") == "True" else False
        if not seeking_venue_data:
            seeking_description_data = None
        else:
            seeking_description_data = form_data.get("seeking_description")
        new_artist = Artist(
            name=form_data.get("name"),
            city=form_data.get("city"),
            state=form_data.get("state"),
            phone=form_data.get("phone"),
            genres=form_data.getlist("genres"),
            image_link=form_data.get("image_link"),
            website=form_data.get("website"),
            seeking_venue=seeking_venue_data,
            seeking_description=seeking_description_data
        )
        db.session.add(new_artist)
        db.session.commit()
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Artist ' + form_data.get("name") + ' could not be listed.')
        return render_template('pages/home.html')
    else:
        flash('Artist ' + form_data.get("name") + ' was successfully listed!')
        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    data = [show.show_details() for show in Show.query.order_by(Show.start_time.desc()).all()]
    return render_template('pages/shows.html', shows=data)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    # TODO: insert form data as a new Show record in the db, instead
    error = False
    try:
        form = ShowForm()
        form_data = request.form
        artist = Artist.query.get(form_data.get('artist_id'))
        if not artist:
            flash(f"Artist with given id {form_data.get('artist_id')} not exists!!!")
            return redirect('/shows/create')
        venue = Venue.query.get(form_data.get('venue_id'))
        if not venue:
            flash(f"Venue with given id {form_data.get('venue_id')} not exists!!!")
            return redirect('/shows/create')
        new_show = Show(
            venue_id=form_data.get('venue_id'),
            artist_id=form_data.get('artist_id'),
            start_time=form_data.get('start_time')
        )
        db.session.add(new_show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        error = True
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()

    if error:
        flash('An error occurred. Show could not be listed.')
    return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

# ----------------------------------------------------------------------------#
# Launch.
# ----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
