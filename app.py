import io
from flask import Flask, render_template, request, session, redirect, Response
from flask_session import Session
from helpers import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

STARTING_MONEY = 100
PROBABILITY_LOWER = 0.5
PROBABILITY_UPPER = 0.9

if __name__ == '__main__':
    app = Flask(__name__)
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_TYPE"] = "filesystem"
    Session(app)
    app.run()

# configuration page
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template("index.html")
    elif request.method == "POST":
        process_round_input()
        set_variables()
        return render_template("bet.html")

def set_variables():
    session["money"] = STARTING_MONEY
    session["optimal_money"] = STARTING_MONEY
    session["third_kelly_money"] = STARTING_MONEY
    session["round"] = 1
    session["probability"] = random.uniform(PROBABILITY_LOWER, PROBABILITY_UPPER)
    session["y1"] = [STARTING_MONEY]
    session["y2"] = [STARTING_MONEY]
    session["y3"] = [STARTING_MONEY]

# handles exceptions and bad input
def process_bet_input():
    try:
        session["bet"] = float(request.form.get("input_bet"))
        money = session.get("money")
        if session["bet"] < 0 or session["bet"] > money:
            return f"Enter a number between 0 and {money}"
    except ValueError:
        return "Enter a number."

def process_round_input():
    try:
        session["rounds"] = float(request.form.get("input_round"))
    except ValueError:
        session["rounds"] = 10

# converts session variables to ints
def format_numbers():
    session["money"] = int(session.get("money"))
    session["optimal_money"] = int(session.get("optimal_money"))
    session["rounds"] = int(session.get("rounds"))

def run_remaining_rounds():
    session["bet"] = 0
    while session["round"] <= session["rounds"]:
        get_bet_sizes()
        heads = coin_flip(session.get("probability"))
        update_money(heads)
        session["round"] += 1

# all the matplotlib code
def create_figure():
    x = [n for n in range(0, session.get("rounds") + 1)]  # x axis (round numbers)

    fig = plt.figure(figsize=(6, 4))
    axes = fig.add_axes([0.1, 0.1, 0.8, 0.8])  # left, bottom, width, height (as 0-1)

    axes.set_xlim(0, max(x) * 1.1)
    axes.set_ylim(0, 1.1 * max(*session.get("y1"), *session.get("y2"), *session.get("y3")))
    x_step_size = len(x) // 14 # limits to 15 ticks
    if x_step_size == 0:
        x_step_size = 1
    axes.set_xticks(x[::x_step_size])

    axes.plot(x, session.get("y1"), label="Player")
    axes.plot(x, session.get("y2"), label="Kelly")
    axes.plot(x, session.get("y3"), label="1/3 Kelly")

    plt.xlabel("Rounds")
    plt.ylabel("Money")

    axes.legend(loc=0)  # loc=0 puts legend in the top right

    rounds = session.get("rounds")
    plt.title(f"Returns over {rounds} rounds")

    return fig

def update_money(heads):
    if heads:
        session["money"] += session.get("bet")
        session["optimal_money"] += round(session.get("optimal_bet"), 0)
        session["third_kelly_money"] += round(session.get("third_kelly_bet"), 0)
    else:
        session["money"] -= session.get("bet")
        session["optimal_money"] -= round(session.get("optimal_bet"), 0)
        session["third_kelly_money"] -= round(session.get("third_kelly_bet"), 0)
    session["y1"].append(session.get("money"))
    session["y2"].append(session.get("optimal_money"))
    session["y3"].append(session.get("third_kelly_money"))
    format_numbers()

def get_bet_sizes():
    session["optimal_bet"] = (2 * session.get("probability") - 1) * session.get("optimal_money")
    session["third_kelly_bet"] = session["optimal_bet"] / 3


# game screen
@app.route("/bet", methods=["POST"])
def bet():
    process = process_bet_input() # this method returns error messages
    if process is None:
        heads = coin_flip(session.get("probability"))
        get_bet_sizes() # gets bets of automated betting strategies
        update_money(heads) # updates money of all strategies
        msg = "Heads" if heads else "Tails"
        session["round"] += 1
    else:
        msg = process
    if session.get("money") == 0:
        run_remaining_rounds()
        return redirect("/results")
    # show results screen if finished with every round
    if session.get("round") > session.get("rounds"):
        return redirect("/results")
    return render_template("bet.html", message=msg)

# results screen
@app.route("/results")
def results():
    growth_rate = get_growth_rate(STARTING_MONEY, session.get("money"), session.get("rounds"))
    kelly_growth_rate = get_growth_rate(STARTING_MONEY, session.get("optimal_money"), session.get("rounds"))
    create_figure()
    return render_template("results.html", growth_rate=growth_rate, kelly_growth_rate=kelly_growth_rate, plot_url="/static/images/plot.png")

@app.route("/plot.png")
def plot_png():
    fig = create_figure()
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype="image/png")