from deep_rl import *

def ddpg_continuous(game, log_dir=None, **kwargs):
    config = Config()
    kwargs.setdefault('gate', F.tanh)
    kwargs.setdefault('tag', ddpg_continuous.__name__)
    kwargs.setdefault('q_l2_weight', 0)
    kwargs.setdefault('reward_scale', 1.0)
    kwargs.setdefault('option_epsilon', LinearSchedule(0))
    kwargs.setdefault('action_based_noise', True)
    kwargs.setdefault('noise', OrnsteinUhlenbeckProcess)
    kwargs.setdefault('std', LinearSchedule(0.2))
    config.merge(kwargs)
    if log_dir is None:
        log_dir = get_default_log_dir(kwargs['tag'])

    config.task_fn = lambda **kwargs: Roboschool(game, **kwargs)
    config.evaluation_env = config.task_fn(log_dir=log_dir)

    config.network_fn = lambda state_dim, action_dim: DeterministicActorCriticNet(
        state_dim, action_dim,
        actor_body=FCBody(state_dim, (300, 200), gate=config.gate),
        critic_body=TwoLayerFCBodyWithAction(
            state_dim, action_dim, (400, 300), gate=config.gate),
        actor_opt_fn=lambda params: torch.optim.Adam(params, lr=1e-4),
        critic_opt_fn=lambda params: torch.optim.Adam(
            params, lr=1e-3, weight_decay=config.q_l2_weight)
        )

    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.reward_normalizer = RescaleNormalizer(kwargs['reward_scale'])
    config.random_process_fn = lambda action_dim: config.noise(size=(action_dim, ), std=config.std)
    config.max_steps = 1e6
    config.evaluation_episodes_interval = int(1e4)
    config.evaluation_episodes = 20
    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.logger = get_logger()
    run_episodes(DDPGAgent(config))

def plan_ddpg(game, log_dir=None, **kwargs):
    config = Config()
    kwargs.setdefault('gate', F.tanh)
    kwargs.setdefault('tag', ddpg_continuous.__name__)
    kwargs.setdefault('reward_scale', 1.0)
    kwargs.setdefault('noise', OrnsteinUhlenbeckProcess)
    kwargs.setdefault('std', LinearSchedule(0.2))
    kwargs.setdefault('depth', 2)
    kwargs.setdefault('critic_loss_weight', 10)
    kwargs.setdefault('num_actors', 5)
    kwargs.setdefault('detach_action', True)
    config.merge(kwargs)
    if log_dir is None:
        log_dir = get_default_log_dir(kwargs['tag'])

    config.task_fn = lambda **kwargs: Roboschool(game, **kwargs)
    config.evaluation_env = config.task_fn(log_dir=log_dir)

    config.network_fn = lambda state_dim, action_dim: PlanEnsembleDeterministicNet(
        state_dim, action_dim,
        phi_body=FCBody(state_dim, (400, ), gate=F.tanh),
        num_actors=config.num_actors,
        discount=config.discount,
        detach_action=config.detach_action)
    config.optimizer_fn = lambda params: torch.optim.Adam(params, lr=1e-4)

    config.replay_fn = lambda: Replay(memory_size=1000000, batch_size=64)
    config.discount = 0.99
    config.reward_normalizer = RescaleNormalizer(kwargs['reward_scale'])
    config.random_process_fn = lambda action_dim: config.noise(size=(action_dim, ), std=config.std)
    config.max_steps = 1e6
    config.evaluation_episodes_interval = int(1e4)
    config.evaluation_episodes = 20
    # config.evaluation_episodes = 1
    config.min_memory_size = 64
    config.target_network_mix = 1e-3
    config.logger = get_logger()
    run_episodes(PlanDDPGAgent(config))

def single_run(run, game, fn, tag, **kwargs):
    random_seed()
    log_dir = './log/ensemble-%s/%s/%s-run-%d' % (game, fn.__name__, tag, run)
    fn(game, log_dir, tag=tag, **kwargs)

def multi_runs(game, fn, tag, **kwargs):
    kwargs.setdefault('parallel', False)
    kwargs.setdefault('runs', 5)
    runs = np.arange(0, kwargs['runs'])
    if not kwargs['parallel']:
        for run in runs:
            single_run(run, game, fn, tag, **kwargs)
        return
    ps = [mp.Process(target=single_run, args=(run, game, fn, tag), kwargs=kwargs) for run in runs]
    for p in ps:
        p.start()
        time.sleep(1)
    for p in ps: p.join()

def batch_job():
    cf = Config()
    cf.add_argument('--ind1', type=int, default=0)
    cf.add_argument('--ind2', type=int, default=0)
    cf.merge()

    # game = 'RoboschoolHopper-v1'
    #
    # parallel = True
    # def task1():
    #     multi_runs(game, ddpg_continuous, tag='var_test_original',
    #            gate=F.relu, q_l2_weight=0.01, reward_scale=0.1, noise=OrnsteinUhlenbeckProcess, parallel=parallel)
    #
    # def task2():
    #     multi_runs(game, ddpg_continuous, tag='var_test_tanh',
    #            gate=F.tanh, reward_scale=0.1, noise=OrnsteinUhlenbeckProcess, parallel=parallel)
    #
    # def task3():
    #     multi_runs(game, ddpg_continuous, tag='var_test_no_reward_scale',
    #            gate=F.relu, q_l2_weight=0.01, reward_scale=1.0, noise=OrnsteinUhlenbeckProcess, parallel=parallel)
    #
    # def task4():
    #     multi_runs(game, ddpg_continuous, tag='var_test_gaussian_tanh',
    #            gate=F.tanh, reward_scale=0.1, noise=GaussianProcess, parallel=parallel)
    #
    # def task5():
    #     multi_runs(game, ddpg_continuous, tag='var_test_gaussian_no_reward_scale',
    #            gate=F.relu, q_l2_weight=0.01, reward_scale=1.0, noise=GaussianProcess, parallel=parallel)
    #
    # def task6():
    #     multi_runs(game, ddpg_continuous, tag='var_test_gaussian_tanh_no_reward_scale',
    #            gate=F.tanh, reward_scale=0.1, noise=GaussianProcess, parallel=parallel)
    #
    # def task7():
    #     multi_runs(game, ddpg_continuous, tag='var_test_tanh_no_reward_scale',
    #            gate=F.tanh, reward_scale=1.0, noise=OrnsteinUhlenbeckProcess, parallel=parallel)
    #
    # tasks = [task1, task2, task3, task4, task5, task6, task7]
    # tasks[cf.ind1]()

    # games = ['RoboschoolAnt-v1', 'RoboschoolWalker2d-v1', 'RoboschoolHalfCheetah-v1']
    # games = [
    #     'RoboschoolReacher-v1',
    #     'RoboschoolHopper-v1',
    #     'RoboschoolInvertedDoublePendulum-v1'
    # ]
    # games = ['RoboschoolAnt-v1',
    #          'RoboschoolHalfCheetah-v1',
    #          'RoboschoolHopper-v1',
    #          'RoboschoolInvertedDoublePendulum-v1',
    #          'RoboschoolReacher-v1',
    #          'RoboschoolWalker2d-v1',
    #          'RoboschoolInvertedPendulumSwingup-v1']

    # games = ['Walker2DBulletEnv-v0',
    #          'AntBulletEnv-v0',
    #          'HopperBulletEnv-v0',
    #          'RacecarBulletEnv-v0',
    #          'KukaBulletEnv-v0',
    #          'MinitaurBulletEnv-v0']

    # games = [
    #     'RoboschoolAnt-v1',
    #     'RoboschoolHopper-v1',
    #     'RoboschoolWalker2d-v1',
    #     'RoboschoolHalfCheetah-v1',
    #     'RoboschoolReacher-v1',
    #     'RoboschoolHumanoid-v1'
    # ]
    # game = games[cf.ind1]

    # parallel = True
    # def task():
    #     multi_runs(game, ddpg_continuous, tag='original_ddpg', parallel=parallel)
    #     multi_runs(game, ensemble_ddpg, tag='off_policy',
    #                off_policy_actor=True, off_policy_critic=True, parallel=parallel)
    #     multi_runs(game, ensemble_ddpg, tag='half_policy',
    #                off_policy_actor=False, off_policy_critic=True, parallel=parallel)
    #     multi_runs(game, ensemble_ddpg, tag='on_policy',
    #                off_policy_actor=False, off_policy_critic=False, parallel=parallel)
    #
    # task()

    games = [
        'RoboschoolAnt-v1',
        'RoboschoolWalker2d-v1',
    ]
    game = games[cf.ind1]

    parallel = True
    # def task1():
    #     multi_runs(game, ensemble_ddpg, tag='t1b1',
    #                target_beta=1, behavior_beta=1, parallel=parallel)
    #
    # def task2():
    #     multi_runs(game, ensemble_ddpg, tag='t1b0',
    #                target_beta=1, behavior_beta=0, parallel=parallel)
    #
    # def task3():
    #     multi_runs(game, ensemble_ddpg, tag='t0b1',
    #                target_beta=0, behavior_beta=1, parallel=parallel)
    #
    # def task4():
    #     multi_runs(game, ensemble_ddpg, tag='t0b0',
    #                target_beta=0, behavior_beta=0, parallel=parallel)
    #
    # # def task5():
    # #     multi_runs(game, ensemble_ddpg, tag='per_step_decay_10', num_options=10,
    # #                option_type='per_step', random_option_prob=LinearSchedule(1.0, 0, int(1e6)), parallel=parallel)
    # #
    # # def task6():
    # #     multi_runs(game, ensemble_ddpg, tag='per_episode_decay_10', num_options=10,
    # #                option_type='per_episode', random_option_prob=LinearSchedule(1.0, 0, int(1e6)), parallel=parallel)
    #
    # tasks = [task1, task2, task3, task4]
    #
    # tasks[cf.ind2]()

    # games = [
    #     'RoboschoolAnt-v1',
    #     'RoboschoolHopper-v1'
    # ]
    # game = games[cf.ind1]
    #
    # parallel = True
    # runs = 4
    # def task1():
    #     multi_runs(game, ddpg_continuous, tag='constant_exploration_original_ddpg', parallel=parallel,
    #                std_schedules=[LinearSchedule(0.3)], runs=runs)
    #
    # def task2():
    #     multi_runs(game, ddpg_continuous, tag='option_exploration_original_ddpg', parallel=parallel,
    #                option_epsilon=LinearSchedule(0.3, 0, 1e6), action_based_noise=False, runs=runs)
    #
    # def task3():
    #     multi_runs(game, ensemble_ddpg, tag='constant_exploration_off_policy',
    #                std_schedules=[LinearSchedule(0.3)], off_policy_actor=True, off_policy_critic=True,
    #                parallel=parallel, runs=runs)
    #
    # def task4():
    #     multi_runs(game, ensemble_ddpg, tag='option_exploration_off_policy',
    #                option_epsilon=LinearSchedule(0.3, 0, 1e6), action_based_noise=False,
    #                off_policy_actor=True, off_policy_critic=True, parallel=parallel,
    #                runs=runs)
    #
    # tasks = [task1, task2, task3, task4]
    # tasks[cf.ind2]()

if __name__ == '__main__':
    mkdir('data')
    mkdir('data/video')
    mkdir('dataset')
    mkdir('log')
    os.system('export OMP_NUM_THREADS=1')
    os.system('export MKL_NUM_THREADS=1')
    torch.set_num_threads(1)

    game = 'RoboschoolAnt-v1'
    # game = 'RoboschoolWalker2d-v1'
    # game = 'RoboschoolHalfCheetah-v1'
    # game = 'RoboschoolHopper-v1'
    # game = 'RoboschoolHumanoid-v1'
    # game = 'RoboschoolHumanoidFlagrun-v1'
    # game = 'RoboschoolReacher-v1'
    # game = 'RoboschoolHumanoidFlagrunHarder-v1'
    # batch_job()

    plan_ddpg(game)
