import streamlit as st
import sys, random, math, os
import matplotlib.pyplot as plt
import numpy as np
from io import StringIO

def generate_cvrp_instance(n=100, rootPos=1, custPos=2, demandType=3, avgRouteSize=4, instanceID=1, randSeed=42):

    def distance(x,y):
        return math.sqrt((x[0] - y[0])**2 + (x[1] - y[1])**2)

    maxCoord = 1000
    decay = 40

    if demandType > 7 or demandType < 1:
        raise ValueError("Demand type out of range!")

    random.seed(randSeed)
    nSeeds = random.randint(2,6)

    In = {1:(3,5), 2:(5,8), 3:(8,12), 4:(12,16), 5:(16,25), 6:(25,50)}
    if avgRouteSize > 6 or avgRouteSize < 1:
        raise ValueError("Average route size out of range!")

    r = random.uniform(In[avgRouteSize][0], In[avgRouteSize][1])

    instanceName = 'XML'+str(n)+'_'+str(rootPos)+str(custPos)+str(demandType)+str(avgRouteSize)+'_'+ format(instanceID, '02d')

    ### Assign Depot ###
    depot = (-1, -1)
    S = set()

    x_, y_ = (-1, -1)
    if rootPos == 1:
        x_ = random.randint(0, maxCoord)
        y_ = random.randint(0, maxCoord)
    elif rootPos == 2:
        x_ = y_ = int(maxCoord / 2.0)
    elif rootPos == 3:
        x_ = y_ = 0
    else:
        raise ValueError("Depot Positioning out of range!")

    depot = (x_, y_)

    ### Customer Positioning ###
    nRandCust = -1
    if custPos == 3:
        nRandCust = int(n / 2.0)
    elif custPos == 2:
        nRandCust = 0
    elif custPos == 1:
        nRandCust = n
        nSeeds = 0
    else:
        raise ValueError("Customer Positioning out of range!")

    nClustCust = n - nRandCust

    # Generating random customers
    for i in range(1, nRandCust+1):
        x_ = random.randint(0, maxCoord)
        y_ = random.randint(0, maxCoord)
        while (x_, y_) in S or (x_, y_) == depot:
            x_ = random.randint(0, maxCoord)
            y_ = random.randint(0, maxCoord)
        S.add((x_, y_))

    nS = nRandCust
    seeds = []

    # Generation of the clustered customers
    if nClustCust > 0:
        if nClustCust < nSeeds:
            raise ValueError("Too many seeds!")

        # Generate the seeds
        for i in range(nSeeds):
            x_ = random.randint(0, maxCoord)
            y_ = random.randint(0, maxCoord)
            while (x_, y_) in S or (x_, y_) == depot:
                x_ = random.randint(0, maxCoord)
                y_ = random.randint(0, maxCoord)
            S.add((x_, y_))
            seeds.append((x_, y_))
        nS = nS + nSeeds

        # Determine the seed with maximum sum of weights (w.r.t. all seeds)
        maxWeight = 0.0
        for i,j in seeds:
            w_ij = 0.0
            for i_, j_ in seeds:
                w_ij += 2**(-distance((i,j), (i_,j_)) / decay)
            if w_ij > maxWeight:
                maxWeight = w_ij

        norm_factor = 1.0 / maxWeight

        # Generate the remaining customers using Accept-reject method
        while nS < n:
            x_ = random.randint(0, maxCoord)
            y_ = random.randint(0, maxCoord)
            while (x_, y_) in S or (x_, y_) == depot:
                x_ = random.randint(0, maxCoord)
                y_ = random.randint(0, maxCoord)

            weight = 0.0
            for i_, j_ in seeds:
                weight += 2**(-distance((x_, y_), (i_, j_)) / decay)
            weight *= norm_factor
            rand = random.uniform(0,1)

            if rand <= weight:
                S.add((x_, y_))
                nS = nS + 1

    V = [depot] + list(S)

    # Demands
    demandMinValues = [1, 1, 5, 50, 51, 1, 1]
    demandMaxValues = [1, 10, 10, 100, 100, 50, 100]
    demandMin = demandMinValues[demandType - 1]
    demandMax = demandMaxValues[demandType - 1]
    demandMinEvenQuadrant = 51
    demandMaxEvenQuadrant = 100
    demandMinLarge = 50
    demandMaxLarge = 100
    largePerRoute = 1.5
    demandMinSmall = 1
    demandMaxSmall = 10

    D = [] # demands
    sumDemands = 0
    maxDemand = 0

    for i in range(2, n+2):
        j = int((demandMax - demandMin + 1) * random.uniform(0,1) + demandMin)
        if demandType == 6:
            if (V[i - 1][0] < maxCoord/2.0 and V[i - 1][1] < maxCoord/2.0) or (V[i - 1][0] >= maxCoord/2.0 and V[i - 1][1] >= maxCoord/2.0):
                j = int((demandMaxEvenQuadrant - demandMinEvenQuadrant + 1) * random.uniform(0,1) + demandMinEvenQuadrant)
        if demandType == 7:
            if i < (n / r) * largePerRoute:
                j = int((demandMaxLarge - demandMinLarge + 1) * random.uniform(0,1) + demandMinLarge)
            else:
                j = int((demandMaxSmall - demandMinSmall + 1) * random.uniform(0,1) + demandMinSmall)
        D.append(j)
        if j > maxDemand:
            maxDemand = j
        sumDemands = sumDemands + j

    # Generate capacity
    if sumDemands == n:
        capacity = math.floor(r)
    else:
        capacity = max(maxDemand, math.ceil(r * sumDemands / n))

    k = math.ceil(sumDemands / float(capacity))

    # Write instance data to a StringIO object
    from io import StringIO
    f = StringIO()
    f.write('NAME : ' + instanceName + '\n')
    f.write('COMMENT : Generated as the XML100 dataset from the CVRPLIB\n')
    f.write('TYPE : CVRP\n')
    f.write('DIMENSION : ' + str(n+1) + '\n')
    f.write('EDGE_WEIGHT_TYPE : EUC_2D\n')
    f.write('CAPACITY : ' + str(int(capacity)) + '\n')
    f.write('NODE_COORD_SECTION\n')

    for i, v in enumerate(V):
        f.write('{:<4}'.format(i+1) + ' ' + '{:<4}'.format(v[0]) + ' ' + '{:<4}'.format(v[1]) + '\n')

    f.write('DEMAND_SECTION\n')

    if demandType != 6:
        random.shuffle(D)
    D = [0] + D

    for i, d in enumerate(D):
        f.write('{:<4}'.format(i+1) + ' ' + '{:<4}'.format(d) + '\n')

    f.write('DEPOT_SECTION\n1\n-1\nEOF\n')
    instance_data = f.getvalue()
    f.close()

    # Generate the plot
    x = [v[0] for v in V]
    y = [v[1] for v in V]
    x_s = [v[0] for v in seeds]
    y_s = [v[1] for v in seeds]

    fig, ax = plt.subplots(figsize=(8, 8))
    ax.scatter(x[1:], y[1:], marker='o', color='blue', edgecolor='blue', s=40, label='Customers')
    if seeds:
        ax.scatter(x_s, y_s, marker='o', color='magenta', edgecolor='magenta', s=40, label='Seeds')
    ax.scatter([x[0]], [y[0]], marker='s', edgecolor='black', color='yellow', s=200, label='Depot')
    ax.set_xticks([])
    ax.set_yticks([])
    ax.legend()
    ax.set_title('CVRP Instance Visualization')

    # Return the instance data and the figure
    return instance_data, fig

def main():
    st.title("CVRP Instance Generator")
    st.write("Configure the parameters below to generate a CVRP instance.")

    # Parameters
    n = st.number_input("Number of customers (n)", min_value=1, value=100)
    rootPos = st.selectbox("Depot positioning", options=[1,2,3], format_func=lambda x: {1: "Random", 2: "Centered", 3: "Cornered"}[x])
    custPos = st.selectbox("Customer positioning", options=[1,2,3], format_func=lambda x: {1: "Random", 2: "Clustered", 3: "Random-clustered"}[x])
    demandType = st.selectbox("Demand distribution type", options=list(range(1,8)), format_func=lambda x: {
        1: "Unitary",
        2: "Small, large var",
        3: "Small, small var",
        4: "Large, large var",
        5: "Large, small var",
        6: "Large, depending on quadrant",
        7: "Few large, many small"
    }[x])
    avgRouteSize = st.selectbox("Average route size", options=[1,2,3,4,5,6], format_func=lambda x: {
        1: "Very short",
        2: "Short",
        3: "Medium",
        4: "Long",
        5: "Very long",
        6: "Ultra long"
    }[x])
    instanceID = st.number_input("Instance ID", min_value=1, value=1)
    randSeed = st.number_input("Random seed", value=42, format="%d")

    if st.button("Generate Instance"):
        with st.spinner('Generating instance...'):
            instance_data, fig = generate_cvrp_instance(n=int(n), rootPos=rootPos, custPos=custPos, demandType=demandType, avgRouteSize=avgRouteSize, instanceID=int(instanceID), randSeed=int(randSeed))
        st.success('Instance generated!')

        # Display instance data
        st.subheader("Instance Data")
        st.download_button(label="Download .vrp file", data=instance_data, file_name="instance.vrp", mime='text/plain')
        st.text(instance_data)

        # Display plot
        st.subheader("Instance Visualization")
        st.pyplot(fig)

if __name__ == "__main__":
    main()

