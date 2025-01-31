from pytest import importorskip
from eventio.simtel import SimTelFile

prod2_path = 'tests/resources/gamma_test.simtel.gz'
prod3_path = 'tests/resources/gamma_test_large_truncated.simtel.gz'
prod4_path = 'tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.gz'

# using a zstd file ensures SimTelFile is not seeking back, when reading
# a file
prod4_zst_path = 'tests/resources/gamma_20deg_0deg_run102___cta-prod4-sst-1m_desert-2150m-Paranal-sst-1m.simtel.zst'


test_paths = [prod2_path, prod3_path, prod4_path]


def test_can_open():
    for path in test_paths:
        assert SimTelFile(path)


def test_at_least_one_event_found():
    for path in test_paths:
        one_found = False
        for event in SimTelFile(path):
            one_found = True
            break
        assert one_found, path


def test_show_we_get_a_dict_with_hower_and_event():
    for path in test_paths:
        for event in SimTelFile(path):
            assert 'mc_shower' in event
            assert 'telescope_events' in event
            assert 'mc_event' in event
            break


def test_show_event_is_not_empty_and_has_some_members_for_sure():
    for path in test_paths:
        for event in SimTelFile(path):
            assert event['mc_shower'].keys() == {
                'shower',
                'primary_id',
                'energy',
                'azimuth',
                'altitude',
                'depth_start',
                'h_first_int',
                'xmax',
                'hmax',
                'emax',
                'cmax',
                'n_profiles',
                'profiles'
            }

            print(event.keys())
            assert event.keys() == {
                'event_id',
                'mc_shower',
                'mc_event',
                'telescope_events',
                'trigger_information',
                'tracking_positions',
                'photoelectron_sums',
                'photoelectrons',
                'camera_monitorings',
                'laser_calibrations',
            }

            telescope_events = event['telescope_events']

            assert telescope_events  # never empty!

            for telescope_event in telescope_events.values():
                expected_keys = {
                    'header',
                    'pixel_timing',
                    'pixel_lists',
                }
                allowed_keys = {
                    'image_parameters',
                    'adc_sums',
                    'adc_samples'
                }

                found_keys = set(telescope_event.keys())
                assert expected_keys.issubset(found_keys)

                extra_keys = found_keys.difference(expected_keys)
                assert extra_keys.issubset(allowed_keys)
                assert 'adc_sums' in found_keys or 'adc_samples' in found_keys

            break


def test_iterate_complete_file():
    expected_counter_values = {
        prod2_path: 8,
        prod3_path: 5,
        prod4_path: 30,
    }
    for path, expected in expected_counter_values.items():
        try:
            for counter, event in enumerate(SimTelFile(path)):
                pass
        except (EOFError, IndexError):  # truncated files might raise these...
            pass
        assert counter == expected


def test_iterate_complete_file_zst():
    importorskip('zstandard')
    expected = 30
    try:
        for counter, event in enumerate(SimTelFile(prod4_zst_path)):
            pass
    except (EOFError, IndexError):  # truncated files might raise these...
        pass
    assert counter == expected


def test_iterate_mc_events():
    expected = 200
    try:
        with SimTelFile(prod4_path) as f:
            for counter, event in enumerate(f.iter_mc_events(), start=1):
                pass
    except (EOFError, IndexError):  # truncated files might raise these...
        pass
    assert counter == expected


def test_allowed_tels():
    allowed_telescopes = {1, 2, 3, 4}
    n_read = 0
    with SimTelFile(prod2_path, allowed_telescopes=allowed_telescopes) as f:
        try:
            for i, event in enumerate(f):
                print(i)
                telescopes = set(event['telescope_events'].keys())
                assert allowed_telescopes.issuperset(telescopes)
                assert telescopes.issubset(allowed_telescopes)
                n_read += 1
        except EOFError:
            pass

    assert n_read == 3
