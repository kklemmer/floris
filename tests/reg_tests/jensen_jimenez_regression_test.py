# Copyright 2020 NREL

# Licensed under the Apache License, Version 2.0 (the "License"); you may not
# use this file except in compliance with the License. You may obtain a copy of
# the License at http://www.apache.org/licenses/LICENSE-2.0

# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations under
# the License.

# See https://floris.readthedocs.io for documentation

import numpy as np

from tests.conftest import N_TURBINES, N_WIND_DIRECTIONS, N_WIND_SPEEDS, print_test_values, assert_results_arrays
from floris.simulation import Ct, Floris, power, axial_induction, average_velocity


DEBUG = False
VELOCITY_MODEL = "jensen"
DEFLECTION_MODEL = "jimenez"


baseline = np.array(
    [
        # 8 m/s
        [
            [7.9803783, 0.7634300, 1695368.6455473, 0.2568077],
            [6.1586693, 0.8281095, 771695.5183645, 0.2927016],
            [5.6649575, 0.8525678, 591183.4224051, 0.3080155],
        ],
        # 9 m/s
        [
            [8.9779256, 0.7625731, 2413659.0651694, 0.2563676],
            [6.9320149, 0.7949935, 1111075.5222317, 0.2736118],
            [6.5096913, 0.8119868, 914506.7978006, 0.2831975],
        ],
        # 10 m/s
        [
            [9.9754729, 0.7527803, 3306006.9741814, 0.2513940],
            [7.7463403, 0.7694798, 1555119.6348506, 0.2599374],
            [7.3515939, 0.7807184, 1328908.6335441, 0.2658625],
        ],
        # 11 m/s
        [
            [10.9730201, 0.7304328, 4373591.7174990, 0.2404007],
            [8.6282011, 0.7618323, 2145598.3751232, 0.2559879],
            [8.1492048, 0.7625163, 1808647.8917100, 0.2563385],
        ]
    ]
)

yawed_baseline = np.array(
    [
        # 8 m/s
        [
            [7.9803783, 0.7605249, 1683956.3885389, 0.2548147],
            [6.1728072, 0.8274579, 777423.9137261, 0.2923090],
            [5.6709666, 0.8522603, 593267.9301046, 0.3078154],
        ],
        # 9 m/s
        [
            [8.9779256, 0.7596713, 2397237.3791443, 0.2543815],
            [6.9478646, 0.7943557, 1118452.7210795, 0.2732599],
            [6.5163235, 0.8117199, 917593.7253615, 0.2830437],
        ],
        # 10 m/s
        [
            [9.9754729, 0.7499157, 3283592.6005045, 0.2494847],
            [7.7632705, 0.7690422, 1565265.2188750, 0.2597097],
            [7.3579086, 0.7805112, 1332252.5927338, 0.2657518],
        ],
        # 11 m/s
        [
            [10.9730201, 0.7276532, 4344217.6993801, 0.2386508],
            [ 8.6452693, 0.7618684, 2158680.9632462, 0.2560064],
            [ 8.1535164, 0.7625046, 1811581.5799780, 0.2563325],
        ]
    ]
)

# Note: compare the yawed vs non-yawed results. The upstream turbine
# power should be lower in the yawed case. The following turbine
# powers should higher in the yawed case.


def test_regression_tandem(sample_inputs_fixture):
    """
    Tandem turbines
    """
    sample_inputs_fixture.floris["wake"]["model_strings"]["velocity_model"] = VELOCITY_MODEL
    sample_inputs_fixture.floris["wake"]["model_strings"]["deflection_model"] = DEFLECTION_MODEL

    floris = Floris.from_dict(sample_inputs_fixture.floris)
    floris.steady_state_atmospheric_condition()

    n_turbines = floris.farm.n_turbines
    n_wind_speeds = floris.flow_field.n_wind_speeds
    n_wind_directions = floris.flow_field.n_wind_directions

    velocities = floris.flow_field.u
    yaw_angles = floris.farm.yaw_angles
    test_results = np.zeros((n_wind_directions, n_wind_speeds, n_turbines, 4))

    farm_avg_velocities = average_velocity(
        velocities,
    )
    farm_cts = Ct(
        velocities,
        yaw_angles,
        floris.turbine.fCt_interp,
    )
    farm_powers = power(
        floris.flow_field.air_density,
        velocities,
        yaw_angles,
        floris.turbine.pP,
        floris.turbine.power_interp,
    )
    farm_axial_inductions = axial_induction(
        velocities,
        yaw_angles,
        floris.turbine.fCt_interp,
    )
    for i in range(n_wind_directions):
        for j in range(n_wind_speeds):
            for k in range(n_turbines):
                test_results[i, j, k, 0] = farm_avg_velocities[i, j, k]
                test_results[i, j, k, 1] = farm_cts[i, j, k]
                test_results[i, j, k, 2] = farm_powers[i, j, k]
                test_results[i, j, k, 3] = farm_axial_inductions[i, j, k]

    if DEBUG:
        print_test_values(
            farm_avg_velocities,
            farm_cts,
            farm_powers,
            farm_axial_inductions,
        )

    assert_results_arrays(test_results[0], baseline)


def test_regression_rotation(sample_inputs_fixture):
    """
    Turbines in tandem and rotated.
    The result from 270 degrees should match the results from 360 degrees.

    Wind from the West (Left)

    ^
    |
    y

    1|1         3
     |
     |
     |
    0|0         2
     |----------|
      0         1  x->


    Wind from the North (Top), rotated

    ^
    |
    y

    1|3         2
     |
     |
     |
    0|1         0
     |----------|
      0         1  x->

    In 270, turbines 2 and 3 are waked. In 360, turbines 0 and 2 are waked.
    The test compares turbines 2 and 3 with 0 and 2 from 270 and 360.
    """
    TURBINE_DIAMETER = sample_inputs_fixture.floris["turbine"]["rotor_diameter"]

    sample_inputs_fixture.floris["wake"]["model_strings"]["velocity_model"] = VELOCITY_MODEL
    sample_inputs_fixture.floris["wake"]["model_strings"]["deflection_model"] = DEFLECTION_MODEL
    sample_inputs_fixture.floris["farm"]["layout_x"] = [
        0.0,
        0.0,
        5 * TURBINE_DIAMETER,
        5 * TURBINE_DIAMETER,
    ]
    sample_inputs_fixture.floris["farm"]["layout_y"] = [
        0.0,
        5 * TURBINE_DIAMETER,
        0.0,
        5 * TURBINE_DIAMETER
    ]
    sample_inputs_fixture.floris["flow_field"]["wind_directions"] = [270.0, 360.0]
    sample_inputs_fixture.floris["flow_field"]["wind_speeds"] = [8.0]

    floris = Floris.from_dict(sample_inputs_fixture.floris)
    floris.steady_state_atmospheric_condition()

    farm_avg_velocities = average_velocity(floris.flow_field.u)

    t0_270 = farm_avg_velocities[0, 0, 0]  # upstream
    t1_270 = farm_avg_velocities[0, 0, 1]  # upstream
    t2_270 = farm_avg_velocities[0, 0, 2]  # waked
    t3_270 = farm_avg_velocities[0, 0, 3]  # waked

    t0_360 = farm_avg_velocities[1, 0, 0]  # waked
    t1_360 = farm_avg_velocities[1, 0, 1]  # upstream
    t2_360 = farm_avg_velocities[1, 0, 2]  # waked
    t3_360 = farm_avg_velocities[1, 0, 3]  # upstream

    assert np.allclose(t0_270, t1_360)
    assert np.allclose(t1_270, t3_360)
    assert np.allclose(t2_270, t0_360)
    assert np.allclose(t3_270, t2_360)


def test_regression_yaw(sample_inputs_fixture):
    """
    Tandem turbines with the upstream turbine yawed
    """
    sample_inputs_fixture.floris["wake"]["model_strings"]["velocity_model"] = VELOCITY_MODEL
    sample_inputs_fixture.floris["wake"]["model_strings"]["deflection_model"] = DEFLECTION_MODEL

    floris = Floris.from_dict(sample_inputs_fixture.floris)

    yaw_angles = np.zeros((N_WIND_DIRECTIONS, N_WIND_SPEEDS, N_TURBINES))
    yaw_angles[:,:,0] = 5.0
    floris.farm.yaw_angles = yaw_angles

    floris.steady_state_atmospheric_condition()

    n_turbines = floris.farm.n_turbines
    n_wind_speeds = floris.flow_field.n_wind_speeds
    n_wind_directions = floris.flow_field.n_wind_directions

    velocities = floris.flow_field.u
    yaw_angles = floris.farm.yaw_angles
    test_results = np.zeros((n_wind_directions, n_wind_speeds, n_turbines, 4))

    farm_avg_velocities = average_velocity(
        velocities,
    )
    farm_cts = Ct(
        velocities,
        yaw_angles,
        floris.turbine.fCt_interp,
    )
    farm_powers = power(
        floris.flow_field.air_density,
        velocities,
        yaw_angles,
        floris.turbine.pP,
        floris.turbine.power_interp,
    )
    farm_axial_inductions = axial_induction(
        velocities,
        yaw_angles,
        floris.turbine.fCt_interp,
    )
    for i in range(n_wind_directions):
        for j in range(n_wind_speeds):
            for k in range(n_turbines):
                test_results[i, j, k, 0] = farm_avg_velocities[i, j, k]
                test_results[i, j, k, 1] = farm_cts[i, j, k]
                test_results[i, j, k, 2] = farm_powers[i, j, k]
                test_results[i, j, k, 3] = farm_axial_inductions[i, j, k]

    if DEBUG:
        print_test_values(
            farm_avg_velocities,
            farm_cts,
            farm_powers,
            farm_axial_inductions,
        )

    assert_results_arrays(test_results[0], yawed_baseline)
