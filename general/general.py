from flask import Flask, Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, current_app

BLP_general = Blueprint('BLP_general', __name__,
                        template_folder='templates/general')


@BLP_general.route('/')
def home():
    return render_template('index.html')
