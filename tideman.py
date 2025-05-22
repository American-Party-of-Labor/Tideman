

import copy
import math
import random
import numpy as np
import networkx as nx
from graphviz import Digraph
import random
import tkinter as tk
from tkinter import ttk, messagebox
import pandas
import csv
from PIL import Image, ImageTk
from pathlib import Path
'''
#testing functions, must be commented out when actually in use
def generate_ballot(options):
    r = list(range(1,len(options)+1))
    r = shuffler(r)
    return ballot(options,r)

def maybe_corrupt_ballot(options):
    rand =  random.randint(1,6)
    r = list(range(1,len(options)+1))
    r = shuffler(r)
    r[0] = r[1]
    return ballot(options,r)

'''
def shuffler(list):
    r = list
    random.shuffle(r)
    return r

class Ballot:
    unranked = 1000
    
    def __init__(self, options, rankings):
        self.options = options
        self.rank_validator(rankings)
        self.rankings = rankings
        self.matrix = np.zeros((len(options),len(options)))
        self.ordered_pairs = []
        self.tie_matrix = np.zeros((len(options),len(options)))
    
    def calc_matrix(self):
        for i,o in enumerate(self.options):
            j = i +1
            while j < len(self.options):
                if self.rankings[i] < self.rankings[j]:
                    self.matrix[i,j]-=1
                # rankings can only be equal if both options were unranked
                elif self.rankings[i]==self.rankings[j]:
                    self.tie_matrix[i,j] +=1
                else:
                    self.matrix[i,j]+=1
                j+=1
    # make sure there are no duplicate rankings and rankings are within bounds
    def rank_validator(self,rankings):
        assert len(self.options)==len(rankings)
        already_seen = {}  
        for num in rankings:
                if num!=Ballot.unranked:
                    assert not num in already_seen
                assert num > 0 and (num<=len(self.options) or num==Ballot.unranked)
                already_seen[num]=0
    
class Pair:
    def __init__(self, option_a, option_b, margin):
        self.a = option_a
        self.b = option_b
        self.winner = "ERROR"
        self.loser = "ERROR"
        self.margin = margin

    def __str__(self):
        if self.margin == 0:
            return   self.winner+" tied " + self.loser
        
        return self.winner+" over " + self.loser +" by " +str(self.margin)

class Election:
    def __init__(self,options, num_voters):
        self.ballots = []
        self.pairs = []
        self.options = options
        self.num_voters = max(0,num_voters)
        self.graph = nx.DiGraph()
        self.matrix = np.zeros((len(options),len(options)))
        self.tie_matrix = np.zeros((len(options),len(options)))
        self.image = any
        
    # do not collate matrix until after all ballots are added for security reasons
    def add_ballot(self,blt):
        test_functions_absent = True
        #when in real use, assert that testing ballot functions do not exist
        try:
            generate_ballot
        except NameError:
            pass
        else:
            test_functions_absent = False
        try:
            maybe_corrupt_ballot
        except NameError:
            pass
        else:
            test_functions_absent = False
        assert test_functions_absent
        assert isinstance(blt,Ballot)
        assert len(self.ballots)+1<=self.num_voters
        assert self.ballots.count(blt) == 0
        self.ballots.append(blt)
              
    def collate_matrix(self):
        assert len(self.ballots) == self.num_voters
        #shuffle so that order ballots are added can't be detected
        random.shuffle(self.ballots)
        size = len(self.ballots[0].options)
        self.matrix = np.zeros((size,size))
        for b in self.ballots:
            b.calc_matrix()
            self.matrix+=b.matrix
        #print(e)
            
    def percent_matrix(self):
        # matrix can not be empty
        assert not np.array_equal(self.matrix, np.zeros((len(self.options),len(self.options))))
        m = copy.deepcopy(self.matrix)
        for i,o in enumerate(self.options):
            j = i +1
            while j < len(self.options):
                m[i,j] = self.matrix[i,j]/self.num_voters
    
    def order_pairs(self):
        for i,o in enumerate(self.options):
            j = i +1
            while j < len(self.options):
                p = Pair(self.options[i],self.options[j],np.abs(self.matrix[i][j]))
                if p.margin==0:
                    p.winner = self.options[j]
                    p.loser = self.options[i]
                elif self.matrix[i][j] >0:
                    p.winner = self.options[j]
                    p.loser = self.options[i]
                else:
                    p.winner = self.options[i]
                    p.loser = self.options[j]
                self.pairs.append(p)    
                j+=1
        self.pairs.sort(key=lambda x: x.margin, reverse=True)
        for p in self.pairs:
            print(p)
         
    def build_graph(self):
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(self.options)
        for p in self.pairs:
            # ties aren't added to graph
            if p.margin == 0:
                continue
            
            future = copy.deepcopy(self.graph)
            future.add_edge(p.winner,p.loser)
            if nx.is_directed_acyclic_graph(future):
                self.graph.add_edge(p.winner,p.loser)
            else:
                print("------------------------------------")
                print("Cycle avoided. Excluded edge: " + str(p))
                print("------------------------------------")
         
    def select_winner(self):
        print("")
        no_ancestors = []
        for node in self.graph.nodes():
            a = nx.ancestors(self.graph,node)
            if len(a)==0:
                no_ancestors.append(node)
                
        assert len(no_ancestors)>0
        if len(no_ancestors)==1:
            print("The winner is: "+str(no_ancestors[0]))
        else:
            print("Tied between: "+str([str(node) for node in no_ancestors])) 
                 
    def display_graph(self):
        output = Digraph()
        for node in self.graph.nodes():
            output.node(node,node)
        for edge in self.graph.edges():
            output.edge(edge[0],edge[1])
        output.render("Election-Result-Graph",format="png" )

       

        
    def __str__(self):
        
        s ="      "
        for o in self.options:
            s+= str(o) +" "
        s += "\n"
        for i,row in enumerate(self.matrix):
            s+=str(self.options[i])+" "+str(row)+"\n"
        return s
    
    def build_csv(self):
        assert self.num_voters==len(self.ballots)
        csvfile = open("votes.csv","w",newline="")
        writer = csv.writer(csvfile)
        header = ["candidates"]
        for i in range(1,self.num_voters+1):
            header.append(" vote " +str(i))
        writer.writerow(header)
        for i in range(len(self.options)):
            row = [self.options[i]]
            row += ["       "+str(b.rankings[i]) for b in self.ballots]
            writer.writerow(row)
            
        csvfile.close()


def election_from_cvs():
    csv = pandas.read_csv("votes.csv")
    options = csv.iloc[:,0]
    num_votes = len(csv.iloc[0])-1
    e = Election(options,num_votes)
    for i in range(num_votes):
       e.add_ballot(Ballot(options,list(csv.iloc[0:,i+1])))
    return e

def finialize_election():
    current_election.collate_matrix()
    current_election.order_pairs()
    current_election.build_csv()
    current_election.build_graph()
    current_election.display_graph()
    
    ballot_frame.grid_forget()
    election_setup_frame.grid_forget()
    option_setup_frame.grid_forget()
    separator.grid_forget()
    
    graph_frame = ttk.LabelFrame(root, text="Result Graph", padding=(20, 10))
    graph_frame.grid(row=0, column=2, padx=(20, 10), pady=(20, 10), sticky="nsew", rowspan=3)

    
    photo = ImageTk.PhotoImage(Image.open("Election-Result-Graph.png"))
    canvas = tk.Canvas(graph_frame,width= root.winfo_screenheight()*0.25, height= root.winfo_screenheight()*0.9)
    canvas.grid(row=0,column=0)
    canvas.image = photo
    canvas.create_image(0, 0, anchor=tk.NW,image=photo)
    
    table_frame = ttk.LabelFrame(root, text="Margin of victory of row-option over column-option", padding=(20, 10))
    
    
    # Add a Treeview widget
    header_row = copy.deepcopy(current_election.options)
    header_row.insert(0,"Candidates")

    tree = ttk.Treeview(table_frame, column=header_row, show='headings', height=5)
        
    for candidate in header_row:
        tree.column(candidate, anchor=tk.CENTER)
        tree.heading(candidate, text=candidate)
            
    # Insert the data in Treeview widget
    for i in range(len(current_election.matrix)):
                
        row = ["%d" % -num for num in current_election.matrix[i]]
        row.insert(0,current_election.options[i])
        tree.insert('', 'end', text="1", values=row)

    table_frame.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew", rowspan=3)
    tree.grid(column=0,row=0)

def process_ballot():
    try:
        ballot_frame.config(text="Cast Ballot " + str(len(current_election.ballots)+2) + "/"+str(current_election.num_voters))
        values = [int(entry.get()) for entry in entry_fields]
        b = Ballot(options,values)
        current_election.add_ballot(b)
        if len(current_election.ballots) == current_election.num_voters:
            finialize_election()
        else:
            for entry in entry_fields:
                entry.delete(0, tk.END)
    
       
    except ValueError:
        messagebox.showerror("Input Error", "Please enter positive whole numbers in all input boxes.")
    except AssertionError:
        messagebox.showerror("Input Error", "Reminder no duplicate rankings and rankings range from 1 is best to N is worst for N candidates")
    
def run_ballot_adding():
    
    
    # Create labels and input boxes
    for i in range(len(options)):
        label = ttk.Label(ballot_frame, text=options[i])
        label.grid(row=i, column=0, padx=10, pady=5,sticky="n")
        
        entry = ttk.Entry( ballot_frame)
        entry.grid(row=i, column=1, padx=10, pady=5,sticky="n")
        entry_fields.append(entry)

    # Create a button to check the input and add it to the CVS
    button = ttk.Button( ballot_frame, text="Cast Vote", command=process_ballot)
    button.grid(row=len(options), column=0, columnspan=2, pady=10,sticky="s")
    ballot_frame.config(text="Cast Ballot " + str(len(current_election.ballots)+1) + "/"+str(current_election.num_voters))


def submit_election_setup():
    try:
        o = [str(entry.get()) for entry in option_entries]
        for entry in option_entries:
            if entry.get() == "" or entry.get().replace(" ","")=="":
                messagebox.showerror("Input Error", "No option can be blank")
                return
            if  o.count(str(entry.get()))!=1:
                messagebox.showerror("Input Error", "No duplicate options")
                return
        if int(voters_entry.get()) > 1:
            global options
            options = o
            global current_election
            current_election = Election(shuffler(options),int(voters_entry.get()))
        
        else:
            messagebox.showerror("Input Error", "Must have a positive whole number more than 1 of voters")
            return
    except:
        messagebox.showerror("Input Error", "Invalid election set up")
        return
    run_ballot_adding()

def add_option():
    global num_options
    
    column_size = 8
   
    label = ttk.Label(option_setup_frame, text="Option "+str(num_options+1))
    label.grid(row=num_options%column_size, column=2 * math.floor(num_options/column_size), padx=0, pady=5)
    option_labels.append(label)
    
    entry = ttk.Entry(option_setup_frame)
    entry.grid(row=num_options%column_size, column=1 + 2 * math.floor(num_options/column_size), padx=10, pady=5)
    option_entries.append(entry)
    num_options+=1
    
def remove_option():
    global num_options
    if num_options >2:
        num_options-=1
        option_entries.pop().destroy()
        option_labels.pop().destroy()
    else:
        messagebox.showerror("Input Error", "Elections must have at least 2 options")
    
    
num_options = 0
options = []
current_election = any
entry_fields = []



root = tk.Tk()
# Import the tcl file
root.state("zoomed")

# get the directory where the script file is
progdir = Path(__file__).parent

# function to get the absolute path of a file relative to the script file
def _path(relpath):
    return progdir / relpath

...

# load the required file using the above function
root.tk.call("source", _path("forest-dark.tcl"))

# Set the theme with the theme_use method
ttk.Style().theme_use('forest-dark')
root.iconbitmap(_path("vote.ico"))
   
root.title("Election Setup")
root.option_add("*tearOff", False)
    
root.columnconfigure(index=0, weight=3)
root.columnconfigure(index=1, weight=1)

    
root.rowconfigure(index=0, weight=1)
root.rowconfigure(index=1, weight=1)
root.rowconfigure(index=2, weight=1)
    
 
    
election_setup_frame = ttk.LabelFrame(root, text="Election Setup", padding=(20, 10))
election_setup_frame.grid(row=0, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew")
    
label = ttk.Label(election_setup_frame, text="Number of voters")
label.grid(row=0, column=0, padx=10, pady=5)
voters_entry = ttk.Entry(election_setup_frame)
voters_entry.grid(row=2, column=0, padx=10, pady=5)

    
add_option_button = ttk.Button(election_setup_frame, text="Add an option", command=add_option)
add_option_button.grid(row=2, column=4, columnspan=2, pady=5)
    
remove_option_button = ttk.Button(election_setup_frame, text="remove an option", command=remove_option)
remove_option_button.grid(row=3, column=4, columnspan=2, pady=5)
    
submit_election_setup_button  = ttk.Button(election_setup_frame, text="Submit Election Setup", command=submit_election_setup,style="Accent.TButton")
submit_election_setup_button.grid(row=4, column=4, columnspan=2, pady=5)
    
separator = ttk.Separator(root)
separator.grid(row=1, column=0, padx=(20, 10), pady=10, sticky="ew")
    
#-----------------------------------------------------------------------------------------------------------------------------------------------------------
option_setup_frame = ttk.LabelFrame(root, text="Option Setup", padding=(20, 10))
option_setup_frame.grid(row=2, column=0, padx=(20, 10), pady=(20, 10), sticky="nsew")
    
    
option_entries = []
option_labels = []
add_option()
add_option()
add_option()
         
#----------------------------------------------------------------------------------------------------   

ballot_frame = ttk.LabelFrame(root, text="Cast Ballot", padding=(20, 10))
ballot_frame.grid(row=0, column=1, padx=(20, 10), pady=(20, 10), sticky="nsew", rowspan=3)
#----------------------------------------------------------------------------------------------------  
   
# Start the Tkinter event loop
root.mainloop()
    

#pyinstaller -F --add-data="forest-dark.tcl:." --icon=vote.ico --add-data="vote.ico:." --noconsole --add-data="forest-dark/*:forest-dark" tideman.py 