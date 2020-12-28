from aztec_diamonds import Diamond


def main():
    # Initialize an empty A(1) diamond and draw it
    diamond = Diamond(order=1)
    diamond.draw()

    # Fill the A(1) diamond with a randomly-oriented domino pair
    diamond.fill_two_by_twos()
    diamond.draw()

    # Then iterate the tiling generation and draw as it grows
    while True:
        diamond.step_tile_generation(draw=True)


if __name__ == '__main__':
    main()
